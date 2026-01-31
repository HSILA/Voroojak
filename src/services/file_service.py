from openai import AsyncOpenAI
from src.config import settings

client = AsyncOpenAI(api_key=settings.openai_api_key)


async def create_vector_store_from_file(file_bytes: bytes, filename: str) -> str:
    """Uploads a file and creates a vector store containing it.

    Returns:
        vector_store_id (str)
    """

    # 1. Upload File
    file_obj = await client.files.create(file=(filename, file_bytes), purpose="assistants")

    # 2. Create Vector Store
    vs = await client.vector_stores.create(name=f"VS-{filename}")

    # 3. Add File to Vector Store
    # This triggers processing
    await client.vector_stores.files.create(vector_store_id=vs.id, file_id=file_obj.id)
    
    # 4. Wait for processing to complete
    import asyncio
    
    # Poll for up to 60 seconds
    for _ in range(30):
        await asyncio.sleep(2)
        
        try:
             updated_vs = await client.vector_stores.retrieve(vector_store_id=vs.id)
             
             if updated_vs.file_counts.completed > 0:
                 break
             if updated_vs.file_counts.failed > 0:
                 raise Exception("File processing failed by OpenAI.")
                 
        except Exception:
            pass
            
    return vs.id
