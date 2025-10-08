"""
FastAPI endpoints for the agentic RAG system.
"""

import os
import asyncio
import json
import logging
import hashlib
from contextlib import asynccontextmanager
from typing import Dict, Any, List, Optional
from datetime import datetime
import uuid

from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.responses import StreamingResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
import uvicorn
from dotenv import load_dotenv

from .security import (
    validate_n8n_request,
    verify_n8n_api_key,
    verify_api_key,
    sanitize_input,
    get_security_info,
    SecurityError,
    security_headers_middleware
)

from .agent import rag_agent, AgentDependencies
from .db_utils import (
    initialize_database,
    close_database,
    create_session,
    get_session,
    add_message,
    get_session_messages,
    test_connection
)
from .graph_utils import initialize_graph, close_graph, test_graph_connection
from .models import (
    ChatRequest,
    ChatResponse,
    SearchRequest,
    SearchResponse,
    StreamDelta,
    ErrorResponse,
    HealthStatus,
    ToolCall,
    OpenAIChatRequest,
    OpenAIChatResponse,
    OpenAIStreamResponse,
    OpenAIModelList,
    OpenAIModel,
    OpenAIChoice,
    OpenAIStreamChoice,
    OpenAIMessage,
    OpenAIUsage
)
from .tools import (
    vector_search_tool,
    graph_search_tool,
    hybrid_search_tool,
    list_documents_tool,
    VectorSearchInput,
    GraphSearchInput,
    HybridSearchInput,
    DocumentListInput
)

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

# Application configuration
APP_ENV = os.getenv("APP_ENV", "development")
APP_HOST = os.getenv("APP_HOST", "127.0.0.1")  # Only listen on localhost
APP_PORT = int(os.getenv("APP_PORT", 8000))
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# Configure logging
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL.upper()),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

# Set debug level for our module during development
if APP_ENV == "development":
    logger.setLevel(logging.DEBUG)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for FastAPI app."""
    # Startup
    logger.info("Starting up agentic RAG API...")
    
    try:
        # Initialize database connections
        await initialize_database()
        logger.info("Database initialized")
        
        # Initialize graph database
        await initialize_graph()
        logger.info("Graph database initialized")
        
        # Test connections
        db_ok = await test_connection()
        graph_ok = await test_graph_connection()
        
        if not db_ok:
            logger.error("Database connection failed")
        if not graph_ok:
            logger.error("Graph database connection failed")
        
        logger.info("Agentic RAG API startup complete")
        
    except Exception as e:
        logger.error(f"Startup failed: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down agentic RAG API...")
    
    try:
        await close_database()
        await close_graph()
        logger.info("Connections closed")
    except Exception as e:
        logger.error(f"Shutdown error: {e}")


# Create FastAPI app
app = FastAPI(
    title="Agentic RAG with Knowledge Graph",
    description="AI agent combining vector search and knowledge graph for tech company analysis",
    version="0.1.0",
    lifespan=lifespan
)

# Configure CORS - allow all origins since API key provides security
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,  # Must be False when allow_origins is ["*"]
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"]  # Allow all headers including Authorization
)

app.add_middleware(GZipMiddleware, minimum_size=1000)

# Add security headers middleware
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    return await security_headers_middleware(request, call_next)


# Include multi-tenant API router
from .api_multi_tenant import router as multi_tenant_router
app.include_router(multi_tenant_router)


# Helper functions for agent execution
async def get_or_create_session(request: ChatRequest) -> str:
    """Get existing session or create new one."""
    if request.session_id:
        session = await get_session(request.session_id)
        if session:
            return request.session_id

    # Create new session with workspace_id if provided
    return await create_session(
        user_id=request.user_id,
        workspace_id=request.workspace_id,
        metadata=request.metadata
    )


async def get_conversation_context(
    session_id: str,
    max_messages: int = 10
) -> List[Dict[str, str]]:
    """
    Get recent conversation context.
    
    Args:
        session_id: Session ID
        max_messages: Maximum number of messages to retrieve
    
    Returns:
        List of messages
    """
    messages = await get_session_messages(session_id, limit=max_messages)
    
    return [
        {
            "role": msg["role"],
            "content": msg["content"]
        }
        for msg in messages
    ]


def extract_tool_calls(result) -> List[ToolCall]:
    """
    Extract tool calls from Pydantic AI result.
    
    Args:
        result: Pydantic AI result object
    
    Returns:
        List of ToolCall objects
    """
    tools_used = []
    
    try:
        # Get all messages from the result
        messages = result.all_messages()
        
        for message in messages:
            if hasattr(message, 'parts'):
                for part in message.parts:
                    # Check if this is a tool call part
                    if part.__class__.__name__ == 'ToolCallPart':
                        try:
                            # Debug logging to understand structure
                            logger.debug(f"ToolCallPart attributes: {dir(part)}")
                            logger.debug(f"ToolCallPart content: tool_name={getattr(part, 'tool_name', None)}")
                            
                            # Extract tool information safely
                            tool_name = str(part.tool_name) if hasattr(part, 'tool_name') else 'unknown'
                            
                            # Get args - the args field is a JSON string in Pydantic AI
                            tool_args = {}
                            if hasattr(part, 'args') and part.args is not None:
                                if isinstance(part.args, str):
                                    # Args is a JSON string, parse it
                                    try:
                                        import json
                                        tool_args = json.loads(part.args)
                                        logger.debug(f"Parsed args from JSON string: {tool_args}")
                                    except json.JSONDecodeError as e:
                                        logger.debug(f"Failed to parse args JSON: {e}")
                                        tool_args = {}
                                elif isinstance(part.args, dict):
                                    tool_args = part.args
                                    logger.debug(f"Args already a dict: {tool_args}")
                            
                            # Alternative: use args_as_dict method if available
                            if hasattr(part, 'args_as_dict'):
                                try:
                                    tool_args = part.args_as_dict()
                                    logger.debug(f"Got args from args_as_dict(): {tool_args}")
                                except:
                                    pass
                            
                            # Get tool call ID
                            tool_call_id = None
                            if hasattr(part, 'tool_call_id'):
                                tool_call_id = str(part.tool_call_id) if part.tool_call_id else None
                            
                            # Create ToolCall with explicit field mapping
                            tool_call_data = {
                                "tool_name": tool_name,
                                "args": tool_args,
                                "tool_call_id": tool_call_id
                            }
                            logger.debug(f"Creating ToolCall with data: {tool_call_data}")
                            tools_used.append(ToolCall(**tool_call_data))
                        except Exception as e:
                            logger.debug(f"Failed to parse tool call part: {e}")
                            continue
    except Exception as e:
        logger.warning(f"Failed to extract tool calls: {e}")
    
    return tools_used


async def save_conversation_turn(
    session_id: str,
    user_message: str,
    assistant_message: str,
    metadata: Optional[Dict[str, Any]] = None
):
    """
    Save a conversation turn to the database.
    
    Args:
        session_id: Session ID
        user_message: User's message
        assistant_message: Assistant's response
        metadata: Optional metadata
    """
    # Save user message
    await add_message(
        session_id=session_id,
        role="user",
        content=user_message,
        metadata=metadata or {}
    )
    
    # Save assistant message
    await add_message(
        session_id=session_id,
        role="assistant",
        content=assistant_message,
        metadata=metadata or {}
    )


async def execute_agent(
    message: str,
    session_id: str,
    user_id: Optional[str] = None,
    workspace_id: Optional[str] = None,
    save_conversation: bool = True
) -> tuple[str, List[ToolCall]]:
    """
    Execute the agent with a message.

    Args:
        message: User message
        session_id: Session ID
        user_id: Optional user ID
        workspace_id: Optional workspace ID
        save_conversation: Whether to save the conversation

    Returns:
        Tuple of (agent response, tools used)
    """
    try:
        # Get workspace_id from session if not provided
        if not workspace_id:
            from .db_utils import db_pool
            async with db_pool.acquire() as conn:
                workspace_id = await conn.fetchval(
                    "SELECT workspace_id::text FROM sessions WHERE id = $1::uuid",
                    session_id
                )

        # Create dependencies
        deps = AgentDependencies(
            session_id=session_id,
            workspace_id=workspace_id
        )
        
        # Get conversation context
        context = await get_conversation_context(session_id)
        
        # Build prompt with context
        full_prompt = message
        if context:
            context_str = "\n".join([
                f"{msg['role']}: {msg['content']}"
                for msg in context[-6:]  # Last 3 turns
            ])
            full_prompt = f"Previous conversation:\n{context_str}\n\nCurrent question: {message}"
        
        # Run the agent
        result = await rag_agent.run(full_prompt, deps=deps)
        
        response = result.data
        tools_used = extract_tool_calls(result)
        
        # Save conversation if requested
        if save_conversation:
            await save_conversation_turn(
                session_id=session_id,
                user_message=message,
                assistant_message=response,
                metadata={
                    "user_id": user_id,
                    "tool_calls": len(tools_used)
                }
            )
        
        return response, tools_used
        
    except Exception as e:
        logger.error(f"Agent execution failed: {e}")
        error_response = f"I encountered an error while processing your request: {str(e)}"
        
        if save_conversation:
            await save_conversation_turn(
                session_id=session_id,
                user_message=message,
                assistant_message=error_response,
                metadata={"error": str(e)}
            )
        
        return error_response, []


# API Endpoints
@app.get("/health", response_model=HealthStatus)
async def health_check():
    """Health check endpoint."""
    try:
        # Test database connections
        db_status = await test_connection()
        graph_status = await test_graph_connection()
        
        # Determine overall status
        if db_status and graph_status:
            status = "healthy"
        elif db_status or graph_status:
            status = "degraded"
        else:
            status = "unhealthy"
        
        return HealthStatus(
            status=status,
            database=db_status,
            graph_database=graph_status,
            llm_connection=True,  # Assume OK if we can respond
            version="0.1.0",
            timestamp=datetime.now()
        )
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=500, detail="Health check failed")


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest, api_key: str = Depends(verify_api_key)):
    """Non-streaming chat endpoint."""
    try:
        # Get or create session
        session_id = await get_or_create_session(request)
        
        # Execute agent
        response, tools_used = await execute_agent(
            message=request.message,
            session_id=session_id,
            user_id=request.user_id,
            workspace_id=request.workspace_id
        )
        
        return ChatResponse(
            message=response,
            session_id=session_id,
            tools_used=tools_used,
            metadata={"search_type": str(request.search_type)}
        )
        
    except Exception as e:
        logger.error(f"Chat endpoint failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/chat/stream")
async def chat_stream(request: ChatRequest, api_key: str = Depends(verify_api_key)):
    """Streaming chat endpoint using Server-Sent Events."""
    try:
        # Get or create session
        session_id = await get_or_create_session(request)
        
        async def generate_stream():
            """Generate streaming response using agent.iter() pattern."""
            try:
                yield f"data: {json.dumps({'type': 'session', 'session_id': session_id})}\n\n"
                
                # Create dependencies
                deps = AgentDependencies(
                    session_id=session_id,
                    user_id=request.user_id
                )
                
                # Get conversation context
                context = await get_conversation_context(session_id)
                
                # Build input with context
                full_prompt = request.message
                if context:
                    context_str = "\n".join([
                        f"{msg['role']}: {msg['content']}"
                        for msg in context[-6:]
                    ])
                    full_prompt = f"Previous conversation:\n{context_str}\n\nCurrent question: {request.message}"
                
                # Save user message immediately
                await add_message(
                    session_id=session_id,
                    role="user",
                    content=request.message,
                    metadata={"user_id": request.user_id}
                )
                
                full_response = ""
                
                # Stream using agent.iter() pattern
                async with rag_agent.iter(full_prompt, deps=deps) as run:
                    async for node in run:
                        if rag_agent.is_model_request_node(node):
                            # Stream tokens from the model
                            async with node.stream(run.ctx) as request_stream:
                                async for event in request_stream:
                                    from pydantic_ai.messages import PartStartEvent, PartDeltaEvent, TextPartDelta
                                    
                                    if isinstance(event, PartStartEvent) and event.part.part_kind == 'text':
                                        delta_content = event.part.content
                                        yield f"data: {json.dumps({'type': 'text', 'content': delta_content})}\n\n"
                                        full_response += delta_content
                                        
                                    elif isinstance(event, PartDeltaEvent) and isinstance(event.delta, TextPartDelta):
                                        delta_content = event.delta.content_delta
                                        yield f"data: {json.dumps({'type': 'text', 'content': delta_content})}\n\n"
                                        full_response += delta_content
                
                # Extract tools used from the final result
                result = run.result
                tools_used = extract_tool_calls(result)
                
                # Send tools used information
                if tools_used:
                    tools_data = [
                        {
                            "tool_name": tool.tool_name,
                            "args": tool.args,
                            "tool_call_id": tool.tool_call_id
                        }
                        for tool in tools_used
                    ]
                    yield f"data: {json.dumps({'type': 'tools', 'tools': tools_data})}\n\n"
                
                # Save assistant response
                await add_message(
                    session_id=session_id,
                    role="assistant",
                    content=full_response,
                    metadata={
                        "streamed": True,
                        "tool_calls": len(tools_used)
                    }
                )
                
                yield f"data: {json.dumps({'type': 'end'})}\n\n"
                
            except Exception as e:
                logger.error(f"Stream error: {e}")
                error_chunk = {
                    "type": "error",
                    "content": f"Stream error: {str(e)}"
                }
                yield f"data: {json.dumps(error_chunk)}\n\n"
        
        return StreamingResponse(
            generate_stream(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Content-Type": "text/event-stream"
            }
        )
        
    except Exception as e:
        logger.error(f"Streaming chat failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/search/vector")
async def search_vector(request: SearchRequest, api_key: str = Depends(verify_api_key)):
    """Vector search endpoint."""
    try:
        input_data = VectorSearchInput(
            query=request.query,
            limit=request.limit
        )
        
        start_time = datetime.now()
        results = await vector_search_tool(input_data)
        end_time = datetime.now()
        
        query_time = (end_time - start_time).total_seconds() * 1000
        
        return SearchResponse(
            results=results,
            total_results=len(results),
            search_type="vector",
            query_time_ms=query_time
        )
        
    except Exception as e:
        logger.error(f"Vector search failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/search/graph")
async def search_graph(request: SearchRequest, api_key: str = Depends(verify_api_key)):
    """Knowledge graph search endpoint."""
    try:
        input_data = GraphSearchInput(
            query=request.query
        )
        
        start_time = datetime.now()
        results = await graph_search_tool(input_data)
        end_time = datetime.now()
        
        query_time = (end_time - start_time).total_seconds() * 1000
        
        return SearchResponse(
            graph_results=results,
            total_results=len(results),
            search_type="graph",
            query_time_ms=query_time
        )
        
    except Exception as e:
        logger.error(f"Graph search failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/search/hybrid")
async def search_hybrid(request: SearchRequest, api_key: str = Depends(verify_api_key)):
    """Hybrid search endpoint."""
    try:
        input_data = HybridSearchInput(
            query=request.query,
            limit=request.limit
        )
        
        start_time = datetime.now()
        results = await hybrid_search_tool(input_data)
        end_time = datetime.now()
        
        query_time = (end_time - start_time).total_seconds() * 1000
        
        return SearchResponse(
            results=results,
            total_results=len(results),
            search_type="hybrid",
            query_time_ms=query_time
        )
        
    except Exception as e:
        logger.error(f"Hybrid search failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/documents")
async def list_documents_endpoint(
    limit: int = 20,
    offset: int = 0,
    api_key: str = Depends(verify_api_key)
):
    """List documents endpoint."""
    try:
        input_data = DocumentListInput(limit=limit, offset=offset)
        documents = await list_documents_tool(input_data)
        
        return {
            "documents": documents,
            "total": len(documents),
            "limit": limit,
            "offset": offset
        }
        
    except Exception as e:
        logger.error(f"Document listing failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/sessions/{session_id}")
async def get_session_info(session_id: str, api_key: str = Depends(verify_api_key)):
    """Get session information."""
    try:
        session = await get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        return session
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Session retrieval failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# n8n Integration Endpoints
@app.post("/n8n/chat")
async def n8n_chat_webhook(request: Request, api_key: str = Depends(verify_n8n_api_key)):
    """
    n8n-compatible chat webhook endpoint.
    Handles incoming questions from n8n Chat Trigger or Webhook nodes.
    
    Expected input from n8n:
    - chatInput: The user's question (from Chat Trigger)
    - message: Alternative message field
    - sessionId: Optional session ID for conversation continuity
    - userId: Optional user ID
    """
    try:
        # Validate n8n request
        security_info = validate_n8n_request(request)
        
        body = await request.json()
        
        # Sanitize input
        body = sanitize_input(body)
        
        logger.debug(f"n8n webhook received from {security_info['client_ip']}: {body}")
        
        # Extract message from various possible n8n formats
        message = None
        session_id = None
        user_id = None
        
        # Handle n8n Chat Trigger format
        if "chatInput" in body:
            message = body["chatInput"]
        # Handle custom webhook format
        elif "message" in body:
            message = body["message"]
        elif "question" in body:
            message = body["question"]
        else:
            # Try to extract from nested structures
            for key in ["data", "body", "input"]:
                if key in body and isinstance(body[key], dict):
                    nested = body[key]
                    if "chatInput" in nested:
                        message = nested["chatInput"]
                        break
                    elif "message" in nested:
                        message = nested["message"]
                        break
        
        if not message:
            raise HTTPException(
                status_code=400, 
                detail="No message found. Expected 'chatInput', 'message', or 'question' field"
            )
        
        # Extract optional parameters
        session_id = body.get("sessionId") or body.get("session_id")
        user_id = body.get("userId") or body.get("user_id") or "n8n-user"
        
        # Create or get session
        if not session_id:
            session_id = await create_session(
                user_id=user_id,
                metadata={
                    "source": "n8n",
                    "client_ip": security_info["client_ip"],
                    "user_agent": security_info["user_agent"],
                    "timestamp": datetime.now().isoformat(),
                    "api_key_used": api_key != "disabled"
                }
            )
        
        # Execute agent
        response, tools_used = await execute_agent(
            message=message,
            session_id=session_id,
            user_id=user_id,
            save_conversation=True
        )
        
        # Return n8n-compatible response
        return {
            "response": response,
            "sessionId": session_id,
            "userId": user_id,
            "toolsUsed": len(tools_used),
            "tools": [
                {
                    "name": tool.tool_name,
                    "args": tool.args
                }
                for tool in tools_used
            ],
            "timestamp": datetime.now().isoformat()
        }
        
    except SecurityError:
        raise
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"n8n chat webhook failed: {e}")
        return {
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }


@app.post("/n8n/simple")
async def n8n_simple_webhook(request: Request, api_key: str = Depends(verify_n8n_api_key)):
    """
    Simple n8n webhook endpoint for basic question/answer.
    Returns just the response text for simpler n8n workflows.
    """
    try:
        # Validate n8n request
        security_info = validate_n8n_request(request)
        
        body = await request.json()
        body = sanitize_input(body)
        
        # Extract message
        message = body.get("message") or body.get("question") or body.get("chatInput")
        
        if not message:
            raise HTTPException(status_code=400, detail="Missing 'message' field")
        
        # Create temporary session
        session_id = await create_session(
            user_id="n8n-simple",
            metadata={
                "source": "n8n-simple",
                "client_ip": security_info["client_ip"],
                "user_agent": security_info["user_agent"],
                "timestamp": datetime.now().isoformat(),
                "api_key_used": api_key != "disabled"
            }
        )
        
        # Execute agent
        response, _ = await execute_agent(
            message=message,
            session_id=session_id,
            user_id="n8n-simple",
            save_conversation=False  # Don't save for simple endpoint
        )
        
        # Return simple response
        return {"answer": response}
        
    except SecurityError:
        raise
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"n8n simple webhook failed: {e}")
        return {"error": str(e)}


# OpenAI-Compatible Endpoints for Open WebUI integration

@app.get("/v1/models", response_model=OpenAIModelList)
async def list_models(api_key: str = Depends(verify_api_key)):
    """List available models (OpenAI-compatible endpoint)."""
    models = [
        OpenAIModel(
            id="riddly-rag",
            created=int(datetime.now().timestamp()),
            owned_by="riddly"
        ),
        OpenAIModel(
            id="riddly-rag-vector",
            created=int(datetime.now().timestamp()),
            owned_by="riddly"
        ),
        OpenAIModel(
            id="riddly-rag-graph",
            created=int(datetime.now().timestamp()),
            owned_by="riddly"
        )
    ]
    
    return OpenAIModelList(data=models)


async def convert_openai_to_internal(openai_request: OpenAIChatRequest) -> tuple[str, str]:
    """Convert OpenAI request to internal format."""
    # Extract the latest user message
    user_messages = [msg for msg in openai_request.messages if msg.role == "user"]
    if not user_messages:
        raise HTTPException(status_code=400, detail="No user message found")
    
    latest_message = user_messages[-1].content
    
    # Determine search type from model name
    search_type = "hybrid"  # default
    if "vector" in openai_request.model:
        search_type = "vector"
    elif "graph" in openai_request.model:
        search_type = "graph"
    
    return latest_message, search_type


def estimate_tokens(text: str) -> int:
    """Simple token estimation (rough approximation)."""
    return len(text.split()) * 1.3


@app.post("/v1/chat/completions")
async def openai_chat_completions(request: OpenAIChatRequest, raw_request: Request, api_key: str = Depends(verify_api_key)):
    """OpenAI-compatible chat completions endpoint."""
    import time
    start_time = time.time()
    
    try:
        # Debug logging for Open WebUI requests
        client_ip = raw_request.client.host if raw_request.client else "unknown"
        user_agent = raw_request.headers.get("user-agent", "unknown")
        logger.info(f"OpenAI chat completions request from {client_ip} (UA: {user_agent[:50]}...): model={request.model}, stream={request.stream}, messages={len(request.messages)} messages")
        logger.debug(f"Full request: {request.model_dump()}")
        logger.debug(f"Request headers: {dict(raw_request.headers)}")
        
        # Convert request format
        message, search_type = await convert_openai_to_internal(request)
        
        if request.stream:
            logger.info(f"Using streaming response for Open WebUI request: {message[:50]}...")
            # Return streaming response
            return StreamingResponse(
                openai_chat_stream(request, message, search_type),
                media_type="text/event-stream"
            )
        else:
            logger.info(f"Using non-streaming response for Open WebUI request: {message[:50]}...")
            # Execute agent
            response, tools_used = await execute_agent(
                message=message,
                session_id=None,  # OpenAI API typically doesn't use sessions
                user_id="openai-api",
                save_conversation=False
            )
            
            # Estimate token usage
            prompt_tokens = estimate_tokens(message)
            completion_tokens = estimate_tokens(response)
            
            # Build OpenAI-compatible response
            end_time = time.time()
            response_time = end_time - start_time
            logger.info(f"Non-streaming response completed in {response_time:.2f}s - Response length: {len(response)} chars, Tools used: {len(tools_used)}")
            
            final_response = OpenAIChatResponse(
                id=f"chatcmpl-{uuid.uuid4()}",
                created=int(datetime.now().timestamp()),
                model=request.model,
                choices=[
                    OpenAIChoice(
                        index=0,
                        message=OpenAIMessage(role="assistant", content=response),
                        finish_reason="stop"
                    )
                ],
                usage=OpenAIUsage(
                    prompt_tokens=int(prompt_tokens),
                    completion_tokens=int(completion_tokens),
                    total_tokens=int(prompt_tokens + completion_tokens)
                )
            )
            
            logger.debug(f"Final response object: {final_response.model_dump()}")
            return final_response
            
    except Exception as e:
        logger.error(f"OpenAI chat completions failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


async def openai_chat_stream(request: OpenAIChatRequest, message: str, search_type: str):
    """Generate OpenAI-compatible streaming response."""
    import json
    import time
    
    stream_start = time.time()
    chunk_count = 0
    total_chars = 0
    
    logger.info(f"Starting OpenAI streaming for: {message[:50]}... (model: {request.model})")
    
    response_id = f"chatcmpl-{uuid.uuid4()}"
    created = int(datetime.now().timestamp())
    
    try:
        # Start streaming response
        yield f"data: {json.dumps(OpenAIStreamResponse(id=response_id, created=created, model=request.model, choices=[OpenAIStreamChoice(index=0, delta={'role': 'assistant'}, finish_reason=None)]).model_dump())}\n\n"
        
        # Create dependencies
        deps = AgentDependencies(
            session_id=f"openai-stream-{uuid.uuid4()}",
            user_id="openai-api"
        )
        
        full_response = ""
        
        # Stream using agent.iter() pattern
        async with rag_agent.iter(message, deps=deps) as run:
            async for node in run:
                if rag_agent.is_model_request_node(node):
                    # Stream tokens from the model
                    async with node.stream(run.ctx) as request_stream:
                        async for event in request_stream:
                            from pydantic_ai.messages import PartStartEvent, PartDeltaEvent, TextPartDelta
                            
                            if isinstance(event, PartStartEvent) and event.part.part_kind == 'text':
                                delta_content = event.part.content
                                chunk_count += 1
                                total_chars += len(delta_content)
                                logger.debug(f"Stream chunk {chunk_count}: {len(delta_content)} chars")
                                
                                chunk_response = OpenAIStreamResponse(
                                    id=response_id,
                                    created=created,
                                    model=request.model,
                                    choices=[
                                        OpenAIStreamChoice(
                                            index=0,
                                            delta={"content": delta_content},
                                            finish_reason=None
                                        )
                                    ]
                                )
                                yield f"data: {json.dumps(chunk_response.model_dump())}\n\n"
                                full_response += delta_content
                                
                            elif isinstance(event, PartDeltaEvent) and isinstance(event.delta, TextPartDelta):
                                delta_content = event.delta.content_delta
                                chunk_count += 1
                                total_chars += len(delta_content)
                                logger.debug(f"Stream chunk {chunk_count}: {len(delta_content)} chars")
                                
                                chunk_response = OpenAIStreamResponse(
                                    id=response_id,
                                    created=created,
                                    model=request.model,
                                    choices=[
                                        OpenAIStreamChoice(
                                            index=0,
                                            delta={"content": delta_content},
                                            finish_reason=None
                                        )
                                    ]
                                )
                                yield f"data: {json.dumps(chunk_response.model_dump())}\n\n"
                                full_response += delta_content
        
        # Send final chunk
        final_response = OpenAIStreamResponse(
            id=response_id,
            created=created,
            model=request.model,
            choices=[
                OpenAIStreamChoice(
                    index=0,
                    delta={},
                    finish_reason="stop"
                )
            ]
        )
        
        yield f"data: {json.dumps(final_response.model_dump())}\n\n"
        yield "data: [DONE]\n\n"
        
        stream_end = time.time()
        stream_time = stream_end - stream_start
        logger.info(f"Streaming completed: {chunk_count} chunks, {total_chars} total chars, {stream_time:.2f}s total time")
        
    except Exception as e:
        logger.error(f"OpenAI streaming failed: {e}")
        error_response = OpenAIStreamResponse(
            id=response_id,
            created=created,
            model=request.model,
            choices=[
                OpenAIStreamChoice(
                    index=0,
                    delta={"content": f"Error: {str(e)}"},
                    finish_reason="stop"
                )
            ]
        )
        yield f"data: {json.dumps(error_response.model_dump())}\n\n"
        yield "data: [DONE]\n\n"


# Exception handlers
@app.exception_handler(SecurityError)
async def security_exception_handler(request: Request, exc: SecurityError):
    """Handle security exceptions."""
    return HTTPException(status_code=exc.status_code, detail=exc.detail)

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler."""
    logger.error(f"Unhandled exception: {exc}")
    
    return ErrorResponse(
        error=str(exc),
        error_type=type(exc).__name__,
        request_id=str(uuid.uuid4())
    )


# ====================
# Chat Widget Endpoint
# ====================

@app.get("/widget/chat")
async def get_chat_widget():
    """
    Serve the embeddable chat widget HTML.

    Usage: Embed in your app using an iframe:
    <iframe
        src="http://your-api-url/widget/chat?workspace_id=xxx&agent_id=yyy&agent_name=Support"
        width="100%"
        height="600px"
        frameborder="0">
    </iframe>
    """
    widget_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static", "chat-widget.html")
    return FileResponse(widget_path, media_type="text/html")


@app.get("/static/chat-widget.js")
async def get_chat_widget_js():
    """
    Serve the chat widget JavaScript file.

    Usage: Add this script tag to any HTML page:
    <script src="https://botapi.kobra-dataworks.de/static/chat-widget.js"></script>
    """
    js_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static", "chat-widget.js")
    return FileResponse(js_path, media_type="application/javascript")


@app.get("/static/chat-widget-secure.js")
async def get_chat_widget_secure_js():
    """
    Serve the secure chat widget JavaScript file with API key authentication.

    Usage:
    <script>
      window.IHNEN_CHAT_CONFIG = { apiKey: 'your-api-key' };
    </script>
    <script src="https://botapi.kobra-dataworks.de/static/chat-widget-secure.js"></script>
    """
    js_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static", "chat-widget-secure.js")
    return FileResponse(js_path, media_type="application/javascript")


@app.post("/v1/widget/validate")
async def validate_widget_api_key(request: Request):
    """
    Validate API key and return workspace/agent configuration.

    Returns workspace_id, agent_id, agent_name, and subscription status.
    """
    try:
        # Get API key from Authorization header
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            raise HTTPException(401, "Missing or invalid Authorization header")

        api_key = auth_header.replace("Bearer ", "")

        # Get API key info from database
        from .db_utils import db_pool

        async with db_pool.acquire() as conn:
            # Get API key details
            key_row = await conn.fetchrow(
                """
                SELECT ak.*, w.organization_id
                FROM api_keys ak
                JOIN workspaces w ON ak.workspace_id = w.id
                WHERE ak.key_hash = $1 AND ak.is_active = true
                  AND (ak.expires_at IS NULL OR ak.expires_at > NOW())
                """,
                hashlib.sha256(api_key.encode()).hexdigest()
            )

            if not key_row:
                raise HTTPException(401, "Invalid or expired API key")

            workspace_id = str(key_row["workspace_id"])
            org_id = str(key_row["organization_id"])

            # Get organization to check subscription
            org_row = await conn.fetchrow(
                "SELECT plan_tier FROM organizations WHERE id = $1::uuid",
                org_id
            )

            if not org_row:
                raise HTTPException(404, "Organization not found")

            # Check if subscription is active (for now, free tier and above are active)
            subscription_active = org_row["plan_tier"] in ["free", "starter", "pro", "enterprise"]

            # Get default agent for workspace
            agent_row = await conn.fetchrow(
                """
                SELECT id, name FROM agents
                WHERE workspace_id = $1::uuid AND is_active = true
                ORDER BY created_at ASC
                LIMIT 1
                """,
                workspace_id
            )

            if not agent_row:
                raise HTTPException(404, "No active agent found for workspace")

            agent_id = str(agent_row["id"])
            agent_name = agent_row["name"]

            # Update last_used_at for API key
            await conn.execute(
                "UPDATE api_keys SET last_used_at = NOW() WHERE id = $1::uuid",
                key_row["id"]
            )

            return {
                "workspace_id": workspace_id,
                "agent_id": agent_id,
                "agent_name": agent_name,
                "subscription_active": subscription_active,
                "plan_tier": org_row["plan_tier"]
            }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Widget validation error: {e}")
        raise HTTPException(500, f"Validation failed: {str(e)}")


# Development server
if __name__ == "__main__":
    uvicorn.run(
        "agent.api:app",
        host=APP_HOST,
        port=APP_PORT,
        reload=APP_ENV == "development",
        log_level=LOG_LEVEL.lower()
    )