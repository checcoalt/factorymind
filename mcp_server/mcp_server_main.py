import os
import asyncio
from typing import Any, Dict, List, Optional
from mcp.server import Server
from mcp.types import Tool, TextContent
import pymongo
from motor.motor_asyncio import AsyncIOMotorClient

# Importa i tuoi moduli esistenti
from regression_model import RegressionModel
from rag_system import RAGSystem

class MCPServer:
    def __init__(self):
        self.app = Server("mcp-ml-server")
        self.mongodb_client: Optional[AsyncIOMotorClient] = None
        self.db = None
        
        # Inizializza i tuoi componenti
        self.regression_model = RegressionModel()
        self.rag_system = RAGSystem()
        
        self._register_handlers()
    
    async def connect_mongodb(self):
        """Connette a MongoDB"""
        mongodb_uri = os.getenv("MONGODB_URI", "mongodb://admin:password@localhost:27017/")
        db_name = os.getenv("MONGODB_DB", "mcp_database")
        
        self.mongodb_client = AsyncIOMotorClient(mongodb_uri)
        self.db = self.mongodb_client[db_name]
        
        # Test connessione
        await self.mongodb_client.admin.command('ping')
        print(f"✓ Connesso a MongoDB: {db_name}")
    
    def _register_handlers(self):
        """Registra gli handler per gli strumenti MCP"""
        
        @self.app.list_tools()
        async def list_tools() -> List[Tool]:
            return [
                Tool(
                    name="predict",
                    description="Esegue una predizione usando il modello di regressione",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "features": {
                                "type": "array",
                                "items": {"type": "number"},
                                "description": "Array di feature per la predizione"
                            },
                            "save_to_db": {
                                "type": "boolean",
                                "description": "Se salvare il risultato in MongoDB",
                                "default": False
                            }
                        },
                        "required": ["features"]
                    }
                ),
                Tool(
                    name="query_rag",
                    description="Interroga il sistema RAG per ottenere informazioni",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "Query da sottoporre al RAG"
                            },
                            "top_k": {
                                "type": "integer",
                                "description": "Numero di documenti da recuperare",
                                "default": 5
                            }
                        },
                        "required": ["query"]
                    }
                ),
                Tool(
                    name="store_data",
                    description="Salva dati in MongoDB",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "collection": {
                                "type": "string",
                                "description": "Nome della collezione"
                            },
                            "data": {
                                "type": "object",
                                "description": "Dati da salvare"
                            }
                        },
                        "required": ["collection", "data"]
                    }
                ),
                Tool(
                    name="query_data",
                    description="Interroga dati da MongoDB",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "collection": {
                                "type": "string",
                                "description": "Nome della collezione"
                            },
                            "filter": {
                                "type": "object",
                                "description": "Filtro di query MongoDB",
                                "default": {}
                            },
                            "limit": {
                                "type": "integer",
                                "description": "Numero massimo di risultati",
                                "default": 10
                            }
                        },
                        "required": ["collection"]
                    }
                )
            ]
        
        @self.app.call_tool()
        async def call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
            if name == "predict":
                result = await self._handle_predict(arguments)
            elif name == "query_rag":
                result = await self._handle_rag_query(arguments)
            elif name == "store_data":
                result = await self._handle_store_data(arguments)
            elif name == "query_data":
                result = await self._handle_query_data(arguments)
            else:
                result = {"error": f"Strumento sconosciuto: {name}"}
            
            return [TextContent(type="text", text=str(result))]
    
    async def _handle_predict(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Gestisce le predizioni"""
        try:
            features = args["features"]
            prediction = self.regression_model.predict(features)
            
            result = {
                "prediction": prediction,
                "features": features
            }
            
            # Salva in MongoDB se richiesto
            if args.get("save_to_db", False):
                await self.db.predictions.insert_one(result)
            
            return result
        except Exception as e:
            return {"error": str(e)}
    
    async def _handle_rag_query(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Gestisce le query RAG"""
        try:
            query = args["query"]
            top_k = args.get("top_k", 5)
            
            response = await self.rag_system.query(query, top_k=top_k)
            
            return {
                "query": query,
                "response": response
            }
        except Exception as e:
            return {"error": str(e)}
    
    async def _handle_store_data(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Salva dati in MongoDB"""
        try:
            collection_name = args["collection"]
            data = args["data"]
            
            collection = self.db[collection_name]
            result = await collection.insert_one(data)
            
            return {
                "success": True,
                "inserted_id": str(result.inserted_id)
            }
        except Exception as e:
            return {"error": str(e)}
    
    async def _handle_query_data(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Interroga dati da MongoDB"""
        try:
            collection_name = args["collection"]
            filter_query = args.get("filter", {})
            limit = args.get("limit", 10)
            
            collection = self.db[collection_name]
            cursor = collection.find(filter_query).limit(limit)
            results = await cursor.to_list(length=limit)
            
            # Converti ObjectId in stringa
            for doc in results:
                doc["_id"] = str(doc["_id"])
            
            return {
                "success": True,
                "count": len(results),
                "data": results
            }
        except Exception as e:
            return {"error": str(e)}
    
    async def run(self):
        """Avvia il server MCP"""
        await self.connect_mongodb()
        
        # Avvia il server con stdio transport
        from mcp.server.stdio import stdio_server
        
        async with stdio_server() as (read_stream, write_stream):
            await self.app.run(
                read_stream,
                write_stream,
                self.app.create_initialization_options()
            )

async def main():
    server = MCPServer()
    await server.run()

if __name__ == "__main__":
    asyncio.run(main())