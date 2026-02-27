[ICON]#!/usr/bin/env python3
"""
HPQT Natural Language Assistant
==============================
Ask anything in plain English. The assistant will understand and guide you.

Examples:
- "Where do I find NBA picks?"
- "How do I check high confidence games?"
- "What data is available?"
- "Show me the best bets"
- "How does this work?"
"""

import re
import json
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

class Intent(Enum):
    FIND_DATA = "find_data"
    HOW_TO_USE = "how_to_use"
    WHAT_IS = "what_is"
    SHOW_EXAMPLES = "show_examples"
    GET_HELP = "get_help"
    STATUS_CHECK = "status_check"
    RUN_QUERY = "run_query"
    UNKNOWN = "unknown"

@dataclass
class AssistantResponse:
    """Structured response from the assistant"""
    intent: Intent
    answer: str
    command: Optional[str]
    location: Optional[str]
    examples: List[str]
    related_topics: List[str]

class HPQTAssistant:
    """Natural language interface for the Handicapping Query Tool"""
    
    def __init__(self):
        self.knowledge_base = self._build_knowledge_base()
        self.patterns = self._build_patterns()
        
    def _build_knowledge_base(self) -> Dict:
        """Build comprehensive knowledge base"""
        return {
            "files": {
                "handicapping_query_tool.py": {
                    "location": "sportsbettingprime/handicapping_query_tool.py",
                    "purpose": "Main query tool with all search functions",
                    "usage": "python handicapping_query_tool.py [options]",
                    "features": [
                        "Query by sport (NBA, NFL, NHL, MLB, NCAAF, NCAAB)",
                        "Query by matchup",
                        "Filter by confidence level",
                        "Interactive mode",
                        "Consensus summary"
                    ]
                },
                "covers_contest_picks.csv": {
                    "location": "consensus_library/covers_contest_picks.csv",
                    "purpose": "Main database of all consensus picks",
                    "size": "150KB, 1,250+ records",
                    "columns": ["Game", "Pick", "Sport", "Confidence", "Consensus Count"]
                },
                "picks_database.json": {
                    "location": "consensus_library/picks_database.json",
                    "purpose": "Structured JSON database of picks",
                    "size": "110KB"
                },
                "hpqt_assistant.py": {
                    "location": "sportsbettingprime/hpqt_assistant.py",
                    "purpose": "This assistant - natural language interface",
                    "usage": "python hpqt_assistant.py"
                }
            },
            "commands": {
                "interactive": {
                    "syntax": "python handicapping_query_tool.py --interactive",
                    "description": "Launch interactive query shell",
                    "what_it_does": "Opens a prompt where you can type commands like 'sport NBA' or 'confidence 100'"
                },
                "sport_query": {
                    "syntax": "python handicapping_query_tool.py --sport <SPORT>",
                    "description": "Query picks by sport",
                    "examples": [
                        "--sport NBA",
                        "--sport NFL", 
                        "--sport NHL",
                        "--sport MLB"
                    ]
                },
                "matchup_query": {
                    "syntax": "python handicapping_query_tool.py --matchup <TEAM1> [TEAM2]",
                    "description": "Search for specific team matchups",
                    "examples": [
                        '--matchup "Lakers"',
                        '--matchup "Lakers" "Warriors"',
                        '--matchup "Chiefs"'
                    ]
                },
                "confidence_query": {
                    "syntax": "python handicapping_query_tool.py --confidence <NUMBER>",
                    "description": "Show only high-confidence picks",
                    "examples": [
                        "--confidence 100",
                        "--confidence 150",
                        "--confidence 200"
                    ]
                },
                "summary": {
                    "syntax": "python handicapping_query_tool.py --summary",
                    "description": "Show overall statistics and breakdown"
                },
                "validate": {
                    "syntax": "python handicapping_query_tool.py --validate",
                    "description": "Check if everything is working"
                }
            },
            "workflows": {
                "find_todays_picks": {
                    "steps": [
                        "Run: python handicapping_query_tool.py --interactive",
                        "Type: sport NBA (or your sport)",
                        "Review the picks displayed",
                        "Type: confidence 100 for high-confidence only"
                    ]
                },
                "research_matchup": {
                    "steps": [
                        "Run: python handicapping_query_tool.py --matchup 'TeamName'",
                        "Check the consensus count",
                        "Look for confidence score"
                    ]
                },
                "find_best_bets": {
                    "steps": [
                        "Run: python handicapping_query_tool.py --confidence 150",
                        "This shows only picks with 150+ consensus votes",
                        "Higher number = more people agree"
                    ]
                }
            },
            "concepts": {
                "consensus": "How many people agree on a pick. Higher = more confidence.",
                "confidence_score": "Numerical rating of how strong the consensus is (0-300+).",
                "sharp_consensus": "Picks where experienced bettors agree (usually high confidence).",
                "covers_contest": "Data from Covers.com betting contest - tracks thousands of picks."
            }
        }
    
    def _build_patterns(self) -> List[Tuple[Intent, re.Pattern]]:
        """Build regex patterns for intent recognition"""
        return [
            # FIND DATA patterns
            (Intent.FIND_DATA, re.compile(r"where (?:is|are|can i find|do i find)(?: the)? (.*\?)", re.I)),
            (Intent.FIND_DATA, re.compile(r"how (?:do|can) i (?:find|get|see|access)(?: the)? (.*\?)", re.I)),
            (Intent.FIND_DATA, re.compile(r"show me (?:where|how) (?:to )?(?:find|get) (.*)", re.I)),
            (Intent.FIND_DATA, re.compile(r"location of (.*)", re.I)),
            (Intent.FIND_DATA, re.compile(r"(.*) (?:file|data|database|csv|json) (?:location|where|path)", re.I)),
            
            # HOW TO USE patterns
            (Intent.HOW_TO_USE, re.compile(r"how (?:do|can|should) i (?:use|run|start|launch)(?: the)? (.*\?)", re.I)),
            (Intent.HOW_TO_USE, re.compile(r"how does (.*) work", re.I)),
            (Intent.HOW_TO_USE, re.compile(r"(?:what is|what's) the (?:command|syntax|way) (?:to|for) (.*\?)", re.I)),
            (Intent.HOW_TO_USE, re.compile(r"help (?:me )?(?:with|on|using)? (.*)", re.I)),
            (Intent.HOW_TO_USE, re.compile(r"i want to (.*)", re.I)),
            
            # WHAT IS patterns
            (Intent.WHAT_IS, re.compile(r"what (?:is|are) (.*?)(?:\?|$)", re.I)),
            (Intent.WHAT_IS, re.compile(r"explain (.*)", re.I)),
            (Intent.WHAT_IS, re.compile(r"tell me about (.*)", re.I)),
            
            # SHOW EXAMPLES patterns
            (Intent.SHOW_EXAMPLES, re.compile(r"(?:show|give) me (?:an )?example", re.I)),
            (Intent.SHOW_EXAMPLES, re.compile(r"examples?(?: of| for)? (.*)?", re.I)),
            (Intent.SHOW_EXAMPLES, re.compile(r"how (?:would|do) (?:you|i) (?:use|run) (.*)\?", re.I)),
            
            # GET HELP patterns
            (Intent.GET_HELP, re.compile(r"^(?:help|commands|options|menu)$", re.I)),
            (Intent.GET_HELP, re.compile(r"what (?:can|should) i (?:do|ask|type)", re.I)),
            (Intent.GET_HELP, re.compile(r"list (?:all )?(?:commands|options|features)", re.I)),
            
            # STATUS CHECK patterns
            (Intent.STATUS_CHECK, re.compile(r"(?:is|are) (?:everything|it|this) (?:working|ready|operational)", re.I)),
            (Intent.STATUS_CHECK, re.compile(r"status|check status|system status", re.I)),
            (Intent.STATUS_CHECK, re.compile(r"test|validate|verify", re.I)),
            
            # RUN QUERY patterns
            (Intent.RUN_QUERY, re.compile(r"(?:find|show|get|list) (?:me )?(?:all )?(.*) (?:picks|games|bets)", re.I)),
            (Intent.RUN_QUERY, re.compile(r"(?:nba|nfl|nhl|mlb|ncaa) (?:picks|games|bets)", re.I)),
            (Intent.RUN_QUERY, re.compile(r"best bets|high confidence|sharp picks", re.I)),
        ]
    
    def parse_question(self, question: str) -> Tuple[Intent, str]:
        """Parse user question and determine intent"""
        question = question.strip()
        
        for intent, pattern in self.patterns:
            match = pattern.search(question)
            if match:
                entity = match.group(1).strip() if match.groups() else ""
                return intent, entity
                
        return Intent.UNKNOWN, question
    
    def answer(self, question: str) -> AssistantResponse:
        """Generate answer to user question"""
        intent, entity = self.parse_question(question)
        
        if intent == Intent.FIND_DATA:
            return self._handle_find_data(entity)
        elif intent == Intent.HOW_TO_USE:
            return self._handle_how_to_use(entity)
        elif intent == Intent.WHAT_IS:
            return self._handle_what_is(entity)
        elif intent == Intent.SHOW_EXAMPLES:
            return self._handle_examples(entity)
        elif intent == Intent.GET_HELP:
            return self._handle_help()
        elif intent == Intent.STATUS_CHECK:
            return self._handle_status_check()
        elif intent == Intent.RUN_QUERY:
            return self._handle_run_query(entity)
        else:
            return self._handle_unknown(question)
    
    def _handle_find_data(self, entity: str) -> AssistantResponse:
        """Handle 'where is X' questions"""
        entity_lower = entity.lower()
        
        # Check files
        for filename, info in self.knowledge_base["files"].items():
            if any(keyword in entity_lower for keyword in filename.lower().replace("_", " ").replace(".", " ").split()):
                return AssistantResponse(
                    intent=Intent.FIND_DATA,
                    answer=f"[FILE] Found it! The {info['purpose']}",
                    location=info['location'],
                    command=None,
                    examples=[f"Size: {info.get('size', 'N/A')}"],
                    related_topics=["how to use this file", "what data is inside"]
                )
        
        # Sport-specific queries
        sports = ["nba", "nfl", "nhl", "mlb", "ncaaf", "ncaab", "soccer"]
        for sport in sports:
            if sport in entity_lower:
                return AssistantResponse(
                    intent=Intent.FIND_DATA,
                    answer=f"[SPORT] {sport.upper()} picks are in the main database.",
                    location="consensus_library/covers_contest_picks.csv",
                    command=f"python handicapping_query_tool.py --sport {sport.upper()}",
                    examples=[
                        f"python handicapping_query_tool.py --sport {sport.upper()}",
                        f"python handicapping_query_tool.py --interactive  # Then type: sport {sport.upper()}"
                    ],
                    related_topics=[f"how to filter {sport.upper()} by confidence", "best bets today"]
                )
        
        # General data location
        if any(word in entity_lower for word in ["data", "picks", "games", "bets", "consensus"]):
            return AssistantResponse(
                intent=Intent.FIND_DATA,
                answer="[DATA] All picks data is stored in the consensus_library folder.",
                location="consensus_library/",
                command=None,
                examples=[
                    "covers_contest_picks.csv - Main database (1,250+ records)",
                    "picks_database.json - Structured JSON format"
                ],
                related_topics=["how to query the data", "available sports"]
            )
        
        return AssistantResponse(
            intent=Intent.FIND_DATA,
            answer=f"I'm not sure where '{entity}' is. Here's what I know about:",
            location=None,
            command=None,
            examples=list(self.knowledge_base["files"].keys()),
            related_topics=["list all files", "help"]
        )
    
    def _handle_how_to_use(self, entity: str) -> AssistantResponse:
        """Handle 'how do I use X' questions"""
        entity_lower = entity.lower()
        
        # Check commands
        for cmd_name, cmd_info in self.knowledge_base["commands"].items():
            if cmd_name.replace("_", " ") in entity_lower or any(keyword in entity_lower for keyword in cmd_name.split("_")):
                return AssistantResponse(
                    intent=Intent.HOW_TO_USE,
                    answer=f"[TOOL] {cmd_info['description']}",
                    location=None,
                    command=cmd_info['syntax'],
                    examples=cmd_info.get('examples', [cmd_info['syntax']]),
                    related_topics=["more examples", "what data this returns"]
                )
        
        # Check files/tools
        for filename, info in self.knowledge_base["files"].items():
            if any(part in entity_lower for part in filename.lower().replace("_", " ").split(".")):
                return AssistantResponse(
                    intent=Intent.HOW_TO_USE,
                    answer=f"[DOC] {info['purpose']}",
                    location=info['location'],
                    command=info.get('usage', f"python {filename}"),
                    examples=info.get('features', []),
                    related_topics=["where is this file", "examples"]
                )
        
        # Workflows
        for workflow_name, workflow in self.knowledge_base["workflows"].items():
            if any(word in entity_lower for word in workflow_name.split("_")):
                return AssistantResponse(
                    intent=Intent.HOW_TO_USE,
                    answer=f"[LIST] Here's how to {workflow_name.replace('_', ' ')}:",
                    location=None,
                    command=None,
                    examples=[f"{i+1}. {step}" for i, step in enumerate(workflow['steps'])],
                    related_topics=["related commands", "find data"]
                )
        
        # General usage
        if any(word in entity_lower for word in ["tool", "program", "system", "this"]):
            return AssistantResponse(
                intent=Intent.HOW_TO_USE,
                answer="[TARGET] Quick Start Guide:",
                location=None,
                command="python handicapping_query_tool.py --interactive",
                examples=[
                    "1. Open terminal in sportsbettingprime folder",
                    "2. Run: python handicapping_query_tool.py --interactive",
                    "3. Type: sport NBA (or any sport)",
                    "4. Type: confidence 100 for high-confidence picks",
                    "5. Type: quit to exit"
                ],
                related_topics=["all available commands", "what data is available"]
            )
        
        return AssistantResponse(
            intent=Intent.HOW_TO_USE,
            answer=f"I can help you use the query tool. What would you like to do?",
            location=None,
            command=None,
            examples=[
                "Find NBA picks [ICON] python handicapping_query_tool.py --sport NBA",
                "Interactive mode [ICON] python handicapping_query_tool.py --interactive",
                "High confidence only [ICON] python handicapping_query_tool.py --confidence 150"
            ],
            related_topics=["list all commands", "find data"]
        )
    
    def _handle_what_is(self, entity: str) -> AssistantResponse:
        """Handle 'what is X' questions"""
        entity_lower = entity.lower()
        
        # Check concepts
        for concept_name, definition in self.knowledge_base["concepts"].items():
            if concept_name.replace("_", " ") in entity_lower:
                return AssistantResponse(
                    intent=Intent.WHAT_IS,
                    answer=f"[TIP] {concept_name.replace('_', ' ').title()}: {definition}",
                    location=None,
                    command=None,
                    examples=[],
                    related_topics=["how to use this", "examples"]
                )
        
        # Check files
        for filename, info in self.knowledge_base["files"].items():
            if any(part in entity_lower for part in filename.lower().replace("_", " ").split(".")):
                return AssistantResponse(
                    intent=Intent.WHAT_IS,
                    answer=f"[DOC] {filename}: {info['purpose']}",
                    location=info['location'],
                    command=info.get('usage'),
                    examples=info.get('features', [f"Size: {info.get('size', 'N/A')}"]),
                    related_topics=["how to use this", "where is it"]
                )
        
        # Sports
        sports = ["nba", "nfl", "nhl", "mlb", "ncaaf", "ncaab"]
        if any(sport in entity_lower for sport in sports):
            return AssistantResponse(
                intent=Intent.WHAT_IS,
                answer=f"[SPORT] You can query {entity.upper()} picks using the tool.",
                location="consensus_library/covers_contest_picks.csv",
                command=f"python handicapping_query_tool.py --sport {entity.upper()}",
                examples=[f"python handicapping_query_tool.py --sport {entity.upper()}"],
                related_topics=["how to filter by confidence", "best bets"]
            )
        
        return AssistantResponse(
            intent=Intent.WHAT_IS,
            answer=f"'{entity}' refers to the sports betting consensus data system.",
            location="sportsbettingprime/",
            command="python handicapping_query_tool.py --help",
            examples=[
                "Consensus = collective picks from many bettors",
                "Confidence = how many people agree",
                "Sharp = experienced bettor consensus"
            ],
            related_topics=["how to use the tool", "available commands"]
        )
    
    def _handle_examples(self, entity: str) -> AssistantResponse:
        """Handle example requests"""
        if not entity:
            # General examples
            return AssistantResponse(
                intent=Intent.SHOW_EXAMPLES,
                answer="[BOOK] Common Usage Examples:",
                location=None,
                command=None,
                examples=[
                    "python handicapping_query_tool.py --sport NBA",
                    "python handicapping_query_tool.py --matchup 'Lakers'",
                    "python handicapping_query_tool.py --confidence 150",
                    "python handicapping_query_tool.py --summary",
                    "python handicapping_query_tool.py --interactive"
                ],
                related_topics=["interactive mode commands", "what each command does"]
            )
        
        entity_lower = entity.lower()
        
        # Specific command examples
        for cmd_name, cmd_info in self.knowledge_base["commands"].items():
            if cmd_name.replace("_", " ") in entity_lower:
                return AssistantResponse(
                    intent=Intent.SHOW_EXAMPLES,
                    answer=f"[EXAMPLE] Examples for {cmd_name.replace('_', ' ')}:",
                    location=None,
                    command=cmd_info['syntax'],
                    examples=cmd_info.get('examples', [cmd_info['syntax']]),
                    related_topics=["what this does", "other commands"]
                )
        
        return AssistantResponse(
            intent=Intent.SHOW_EXAMPLES,
            answer=f"[EXAMPLE] Examples for '{entity}':",
            location=None,
            command=None,
            examples=[
                "python handicapping_query_tool.py --interactive",
                "  > sport NBA",
                "  > confidence 100",
                "  > summary",
                "  > quit"
            ],
            related_topics=["all commands", "help"]
        )
    
    def _handle_help(self) -> AssistantResponse:
        """Handle general help requests"""
        return AssistantResponse(
            intent=Intent.GET_HELP,
            answer="[HELP] HPQT Help - Here's what you can do:",
            location=None,
            command=None,
            examples=[
                "QUERIES: --sport NBA | --matchup 'Team' | --confidence 100",
                "MODES: --interactive | --summary | --validate",
                "LOGGING: --log-level DEBUG | --log-file mylog.txt",
                "",
                "Or just ask me: 'Where is X?' | 'How do I Y?' | 'What is Z?'"
            ],
            related_topics=["examples", "find NBA picks", "how to use interactive mode"]
        )
    
    def _handle_status_check(self) -> AssistantResponse:
        """Handle status check requests"""
        return AssistantResponse(
            intent=Intent.STATUS_CHECK,
            answer="[SEARCH] To check if everything is working:",
            location=None,
            command="python handicapping_query_tool.py --validate",
            examples=[
                "This will check:",
                "  [OK] Python version and dependencies",
                "  [OK] Data files are accessible",
                "  [OK] Directory structure is correct",
                "  [OK] Write permissions are available"
            ],
            related_topics=["run test suite", "view logs"]
        )
    
    def _handle_run_query(self, entity: str) -> AssistantResponse:
        """Handle direct query requests"""
        entity_lower = entity.lower()
        
        # Extract sport
        sports = ["nba", "nfl", "nhl", "mlb", "ncaaf", "ncaab", "soccer"]
        for sport in sports:
            if sport in entity_lower:
                return AssistantResponse(
                    intent=Intent.RUN_QUERY,
                    answer=f"[SPORT] Here is the command to get {sport.upper()} picks:",
                    location=None,
                    command=f"python handicapping_query_tool.py --sport {sport.upper()}",
                    examples=[
                        f"python handicapping_query_tool.py --sport {sport.upper()}",
                        f"python handicapping_query_tool.py --sport {sport.upper()} --confidence 100"
                    ],
                    related_topics=["high confidence picks", "interactive mode"]
                )
        
        # Best bets / high confidence
        if any(phrase in entity_lower for phrase in ["best", "high confidence", "sharp", "top"]):
            return AssistantResponse(
                intent=Intent.RUN_QUERY,
                answer="[STAR] To see the best picks (highest confidence):",
                location=None,
                command="python handicapping_query_tool.py --confidence 150",
                examples=[
                    "python handicapping_query_tool.py --confidence 150",
                    "python handicapping_query_tool.py --confidence 200",
                    "Higher numbers = more consensus = sharper picks"
                ],
                related_topics=["what is confidence", "show all sports"]
            )
        
        return AssistantResponse(
            intent=Intent.RUN_QUERY,
            answer="[SEARCH] To search for picks:",
            location=None,
            command="python handicapping_query_tool.py --interactive",
            examples=[
                "Then try these commands:",
                "  sport NBA      [ICON] All NBA picks",
                "  matchup Lakers [ICON] Any game with Lakers",
                "  confidence 100 [ICON] High confidence only",
                "  summary        [ICON] Overall stats"
            ],
            related_topics=["available sports", "how confidence works"]
        )
    
    def _handle_unknown(self, question: str) -> AssistantResponse:
        """Handle unrecognized questions"""
        return AssistantResponse(
            intent=Intent.UNKNOWN,
            answer=f"[UNKNOWN] I'm not sure I understand '{question}'. Try asking:",
            location=None,
            command=None,
            examples=[
                "'Where is the NBA data?'",
                "'How do I use the query tool?'",
                "'Show me examples'",
                "'What is confidence?'",
                "'Find NFL picks'"
            ],
            related_topics=["help", "list commands"]
        )
    
    def format_response(self, response: AssistantResponse) -> str:
        """Format response for display"""
        lines = []
        lines.append("=" * 70)
        lines.append(response.answer)
        lines.append("=" * 70)
        
        if response.location:
            lines.append(f"\n[LOC] Location: {response.location}")
        
        if response.command:
            lines.append(f"\n[CMD] Command:")
            lines.append(f"   {response.command}")
        
        if response.examples:
            lines.append(f"\n[LIST] Examples:")
            for ex in response.examples:
                lines.append(f"   {ex}")
        
        if response.related_topics:
            lines.append(f"\n[TIP] You might also ask:")
            for topic in response.related_topics:
                lines.append(f"   * {topic}")
        
        lines.append("\n" + "=" * 70)
        return "\n".join(lines)

def main():
    """Run the assistant in interactive mode"""
    import sys
    
    assistant = HPQTAssistant()
    
    print("=" * 70)
    print("HPQT NATURAL LANGUAGE ASSISTANT")
    print("=" * 70)
    print("Ask me anything! Examples:")
    print("  * 'Where do I find NBA picks?'")
    print("  * 'How do I use this tool?'")
    print("  * 'Show me examples'")
    print("  * 'What is confidence?'")
    print("  * 'Find high confidence games'")
    print("=" * 70)
    print("Type 'quit' to exit\n")
    
    while True:
        try:
            question = input("[Q] ").strip()
            
            if question.lower() in ['quit', 'exit', 'q', 'bye']:
                print("\n[BYE] Goodbye!")
                break
            
            if not question:
                continue
            
            response = assistant.answer(question)
            print(assistant.format_response(response))
            print()
            
        except KeyboardInterrupt:
            print("\n\n[BYE] Goodbye!")
            break
        except Exception as e:
            print(f"Error: {e}")

if __name__ == '__main__':
    main()
