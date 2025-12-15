"""
Natural Language Formatter for MCP Server Responses
Converts JSON analysis results to human-readable summaries using LangChain + AWS Bedrock.
"""

import json
import os
from typing import Any, Dict, Optional
from langchain_aws import ChatBedrock
from langchain_core.messages import HumanMessage


class NaturalLanguageFormatter:
    """Converts code analysis results to natural language using AWS Bedrock."""
    
    def __init__(
        self,
        model_id: str = "anthropic.claude-3-5-sonnet-20241022-v2:0",
        region: str = "ap-southeast-2",
        enable_summary: bool = True
    ):
        """
        Initialize the formatter.
        
        Args:
            model_id: Bedrock model ID
            region: AWS region
            enable_summary: Whether to enable natural language formatting
        """
        self.model_id = model_id
        self.region = region
        self.enable_summary = enable_summary and os.getenv("ENABLE_NL_FORMAT", "true").lower() == "true"
        self.llm = None
        self._initialized = False
    
    def _initialize(self):
        """Initialize Bedrock client lazily."""
        if not self._initialized and self.enable_summary:
            try:
                self.llm = ChatBedrock(
                    model_id=self.model_id,
                    region_name=self.region,
                    model_kwargs={
                        "max_tokens": 1000,
                        "temperature": 0.3,
                    }
                )
                self._initialized = True
            except Exception as e:
                print(f"⚠️  Failed to initialize Bedrock: {e}")
                self.enable_summary = False
    
    def format_response(self, tool_name: str, result: Any, root_directory: str = "", symbol_name: str = "") -> str:
        """
        Convert analysis result to natural language.
        
        Args:
            tool_name: Name of the tool that produced this result
            result: The analysis result (dict or similar)
            root_directory: Root directory or GitHub URL for context
            symbol_name: Symbol name for context
            
        Returns:
            Natural language formatted response
        """
        # Store context for use in formatting methods
        self._context_root_directory = root_directory
        self._context_symbol_name = symbol_name
        if not self.enable_summary:
            return json.dumps(result, indent=2)
        
        # Normalize common shapes before formatting so tool-specific
        # formatters can rely on dictionaries instead of raw lists.
        original_result = result
        if isinstance(result, list):
            if tool_name == "find_symbol":
                # Deduplicate by (file_path, line_number) for display
                seen = set()
                deduped_result = []
                for occ in result:
                    if isinstance(occ, dict):
                        file_path = occ.get("file_path") or occ.get("file") or occ.get("path")
                        line_num = occ.get("line") or occ.get("line_number")
                        key = (file_path, line_num)
                        if key not in seen:
                            seen.add(key)
                            deduped_result.append(occ)
                original_result = deduped_result
                result = {
                    "symbol": symbol_name or "target symbol",
                    "occurrences": original_result,
                    "count": len(original_result),
                }
            else:
                result = {
                    "items": result,
                    "count": len(result),
                }
        else:
            result = {
                "symbol": symbol_name or "target symbol",
                "occurrences": result,
                "count": len(result),
            }
        
        if not self._initialized:
            self._initialize()
        
        if not self._initialized:
            return json.dumps(original_result, indent=2)
        
        try:
            # Get tool-specific formatter
            formatter_method = getattr(
                self, 
                f"_format_{tool_name}", 
                self._format_generic
            )
            
            # Get the natural language summary
            nl_summary = formatter_method(result)
            
            # Format with both summary and raw data
            formatted = f"{nl_summary}\n\n" + "="*60 + "\nDetailed Results:\n" + "="*60 + "\n"
            formatted += json.dumps(original_result, indent=2)
            
            return formatted
            
        except Exception as e:
            print(f"Error formatting response: {e}")
            return json.dumps(result, indent=2)
    
    def _invoke_bedrock(self, prompt: str) -> str:
        """Invoke Bedrock to generate natural language."""
        try:
            message = HumanMessage(content=prompt)
            response = self.llm.invoke([message])
            return response.content.strip()
        except Exception as e:
            return f"Error generating summary: {e}"
    
    def _format_scan_directory(self, result: Dict) -> str:
        """Format scan_directory results."""
        if not isinstance(result, dict):
            return self._format_generic(result)
        
        prompt = f"""Analyze this code scan result and provide a natural language summary:

{json.dumps(result, indent=2)[:3000]}

Provide a concise summary that includes:
1. Total files analyzed and lines of code
2. Number of functions and classes found
3. Key patterns or structure insights
4. Any notable observations

Format as 3-4 sentences in plain English, suitable for a developer."""
        
        return self._invoke_bedrock(prompt)
    
    def _format_find_symbol(self, result: Dict) -> str:
        """Format find_symbol results."""
        if not isinstance(result, dict):
            return self._format_generic(result)
        
        symbol = result.get("symbol", "target symbol")
        occurrences = result.get("occurrences", [])
        
        # Deduplicate results by (file_path, line_number) keeping the first occurrence
        if isinstance(occurrences, list):
            seen = set()
            deduped_occurrences = []
            for occ in occurrences:
                if isinstance(occ, dict):
                    file_path = occ.get("file_path") or occ.get("file") or occ.get("path")
                    line_num = occ.get("line") or occ.get("line_number")
                    key = (file_path, line_num)
                    if key not in seen:
                        seen.add(key)
                        deduped_occurrences.append(occ)
            occurrences = deduped_occurrences
        
        count = len(occurrences) if isinstance(occurrences, list) else result.get("count", 0)
        
        # Derive unique files
        files = []
        if isinstance(occurrences, list):
            files = list({occ.get("file_path") or occ.get("file") or occ.get("path") for occ in occurrences if isinstance(occ, dict)})
            files = [f for f in files if f]
        distinct_files = len(files)
        
        # Build a concise bullet list for the first few occurrences
        def _format_occ(occ):
            file_path = occ.get("file_path") or occ.get("file") or occ.get("path", "unknown")
            # Replace cached path with root_directory if available
            root_dir = getattr(self, '_context_root_directory', '')
            if root_dir and '/tmp/github_cache/' in file_path:
                # Extract the relative path after the cache hash
                parts = file_path.split('/tmp/github_cache/')[1].split('/', 1)
                if len(parts) > 1:
                    relative_path = parts[1]
                    # Construct the GitHub URL path
                    if root_dir.startswith('https://github.com/'):
                        file_path = f"{root_dir}/blob/HEAD/{relative_path}"
                    else:
                        file_path = relative_path
            line = occ.get("line") or occ.get("line_number")
            context = occ.get("context", "")
            usage_type = occ.get("usage_type", "")
            context_snippet = context[:120] + ("..." if len(context) > 120 else "")
            line_part = f": line {line}" if line is not None else ""
            usage_part = f" [{usage_type}]" if usage_type else ""
            return f"  • {file_path}{line_part}{usage_part} — {context_snippet}".rstrip()
        
        bullet_locations = "\n".join([
            _format_occ(occ)
            for occ in occurrences[:10]
            if isinstance(occ, dict)
        ]) if isinstance(occurrences, list) else ""
        
        summary = f"Found {count} usages of '{symbol}'"
        if distinct_files:
            summary += f" across {distinct_files} file(s)"
        
        if bullet_locations:
            summary += f"\n\nKey locations:\n{bullet_locations}"
        
        if isinstance(occurrences, list) and count > 10:
            summary += f"\n  ... and {count - 10} more"
        
        # For very large results, append a concise Bedrock-generated rollup
        if count > 50 and self._initialized:
            prompt = f"""Summarize symbol usage concisely:

Symbol: {symbol}
Total usages: {count}
Distinct files: {distinct_files}
Sample occurrences:
{json.dumps(occurrences[:10], indent=2)}

Provide 2-3 sentences with key patterns and recommendations."""
            llm_summary = self._invoke_bedrock(prompt)
            if llm_summary and not llm_summary.startswith("Error"):
                summary = f"{summary}\n\nAI summary: {llm_summary}"
        
        return summary
    
    def _format_grep_search(self, result: Dict) -> str:
        """Format grep_search results."""
        if not isinstance(result, dict):
            return self._format_generic(result)
        
        matches = result.get("matches", [])
        pattern = result.get("pattern", "unknown")
        count = len(matches) if isinstance(matches, list) else result.get("count", 0)
        
        if count <= 15:
            # Format small results directly
            locations = "\n".join([
                f"  • {m.get('file', m.get('path', 'unknown'))}: {m.get('line', m.get('context', 'N/A'))}"
                for m in matches[:10]
            ]) if isinstance(matches, list) else ""
            
            summary = f"Found {count} match(es) for pattern '{pattern}'"
            if locations:
                summary += f"\n\nMatching lines:\n{locations}"
            if count > 10:
                summary += f"\n  ... and {count - 10} more"
            
            return summary
        
        # For larger results, use Bedrock
        prompt = f"""Summarize these grep search results:

Pattern: {pattern}
Total Matches: {count}
Sample matches: {json.dumps(matches[:5], indent=2)}

Provide:
1. Total match count
2. File distribution
3. Common pattern in matches
4. Any notable observations

Keep it to 2-3 sentences."""
        
        return self._invoke_bedrock(prompt)
    
    def _format_analyze_impact(self, result: Dict) -> str:
        """Format analyze_impact results."""
        if not isinstance(result, dict):
            return self._format_generic(result)
        
        prompt = f"""Analyze this code impact assessment and summarize:

{json.dumps(result, indent=2)[:2000]}

Highlight:
1. Risk level (low/medium/high)
2. Number of affected areas
3. Type of impact
4. Recommendation

Keep it to 3-4 sentences."""
        
        return self._invoke_bedrock(prompt)
    
    def _format_build_dependency_graph(self, result: Dict) -> str:
        """Format build_dependency_graph results."""
        if not isinstance(result, dict):
            return self._format_generic(result)
        
        prompt = f"""Summarize this dependency graph analysis:

{json.dumps(result, indent=2)[:2500]}

Focus on:
1. Total modules and dependencies
2. Circular dependencies (if any)
3. Coupling issues
4. Architectural health assessment
5. Recommendations

Keep it to 4-5 sentences."""
        
        return self._invoke_bedrock(prompt)
    
    def _format_analyze_and_plan(self, result: Dict) -> str:
        """Format analyze_and_plan results."""
        if not isinstance(result, dict):
            return self._format_generic(result)
        
        plan = result.get("refactoring_plan", "")
        observations = result.get("observations", "")
        
        summary = f"**Refactoring Plan Generated**\n\n"
        
        if observations:
            summary += f"**Key Observations:**\n{observations}\n\n"
        
        if plan:
            # Split plan into sections for bullet points
            lines = plan.split("\n")
            summary += "**Plan Steps:**\n"
            for line in lines[:15]:  # First 15 lines
                if line.strip():
                    summary += f"  • {line.strip()}\n"
            
            if len(lines) > 15:
                summary += f"  ... and {len(lines) - 15} more steps\n"
        
        return summary
    
    def _format_refactor_code(self, result: Dict) -> str:
        """Format refactor_code results."""
        if not isinstance(result, dict):
            return self._format_generic(result)
        
        code = result.get("refactored_code", "")
        improvements = result.get("improvements", [])
        
        summary = f"**Code Refactored**\n\n"
        
        if improvements:
            summary += f"**Improvements Made:**\n"
            for imp in improvements[:5]:
                summary += f"  • {imp}\n"
            if len(improvements) > 5:
                summary += f"  ... and {len(improvements) - 5} more\n\n"
        
        if code:
            lines = code.split("\n")
            summary += f"**Refactored Code ({len(lines)} lines):**\n\n"
            summary += "```python\n"
            summary += "\n".join(lines[:20])
            if len(lines) > 20:
                summary += f"\n... ({len(lines) - 20} more lines)\n"
            summary += "\n```"
        
        return summary
    
    def _format_generate_tests(self, result: Dict) -> str:
        """Format generate_tests results."""
        if not isinstance(result, dict):
            return self._format_generic(result)
        
        tests = result.get("tests", "")
        coverage = result.get("coverage", "unknown")
        
        summary = f"**Test Suite Generated**\n\n"
        summary += f"**Coverage:** {coverage}\n\n"
        
        if tests:
            lines = tests.split("\n")
            test_count = len([l for l in lines if "def test_" in l])
            summary += f"**Test Cases:** {test_count} tests\n\n"
            summary += "```python\n"
            summary += "\n".join(lines[:25])
            if len(lines) > 25:
                summary += f"\n... ({len(lines) - 25} more lines)\n"
            summary += "\n```"
        
        return summary
    
    def _format_generic(self, result: Any) -> str:
        """Generic formatter for unknown tool results."""
        if isinstance(result, dict):
            # Try to extract meaningful info
            keys = list(result.keys())
            summary = f"**Result received** with {len(keys)} field(s):\n"
            for key in keys[:5]:
                value = result[key]
                if isinstance(value, (str, int, float, bool)):
                    summary += f"  • {key}: {value}\n"
                elif isinstance(value, list):
                    summary += f"  • {key}: {len(value)} items\n"
                elif isinstance(value, dict):
                    summary += f"  • {key}: object with {len(value)} fields\n"
            
            if len(keys) > 5:
                summary += f"  ... and {len(keys) - 5} more fields"
            
            return summary
        
        return str(result)
