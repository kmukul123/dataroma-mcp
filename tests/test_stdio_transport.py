import unittest
import subprocess
import json
import os
import sys

class TestStdioTransport(unittest.TestCase):
    def test_mcp_initialization_stdout_purity(self):
        """
        Tests that when the server is launched, it ONLY outputs valid JSON-RPC
        to stdout and does NOT pollute stdout with banners or INFO logs.
        This verifies the fix for the 'Connection closed' issue in Hermes.
        """
        # The standard JSON-RPC initialization request used by MCP clients
        init_request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {
                    "name": "test-client",
                    "version": "1.0.0"
                }
            }
        }
        
        # Determine how to run the module (using uv run or just python)
        # We will invoke it exactly how the entry point works
        server_command = [sys.executable, "-m", "dataroma_mcp"]
        
        try:
            # We launch the server, pipe in the init request, and capture stdout and stderr
            process = subprocess.Popen(
                server_command,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            )
            
            # Send the request and get the output
            request_str = json.dumps(init_request) + "\n"
            stdout_data, stderr_data = process.communicate(input=request_str, timeout=10)
            
            # 1. Assert stdout is NOT empty
            self.assertTrue(stdout_data.strip(), "Server did not output anything to stdout")
            
            # 2. Try parsing the VERY FIRST line of stdout as JSON
            # This will fail if there is an ASCII banner or INFO log at the top of stdout!
            try:
                first_line = stdout_data.strip().split("\n")[0]
                response = json.loads(first_line)
            except json.JSONDecodeError as e:
                self.fail(f"Stdout pollution detected! The first line of stdout was not valid JSON.\\nOutput was: {stdout_data[:200]}...")
            
            # 3. Verify it's a valid JSON-RPC response to our initialization request
            self.assertEqual(response.get("jsonrpc"), "2.0")
            self.assertEqual(response.get("id"), 1)
            self.assertIn("protocolVersion", response.get("result", {}))
            
        except subprocess.TimeoutExpired:
            process.kill()
            self.fail("Server timed out waiting for JSON-RPC initialization")

if __name__ == '__main__':
    unittest.main()
