# problem_loader.py
import json
import logging
import re
import sys
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

class TestCase(dict):
    """Simple wrapper for test case data."""
    input: str
    output: str

class Problem(dict):
    """Simple wrapper for problem data."""
    id: int
    title: str # <--- NEW FIELD
    question: str
    difficulty: str
    public_cases: List[TestCase]
    hidden_cases: List[TestCase]

# This is the original dictionary that main.py imports a reference to.
# We MUST NOT re-assign this variable. We must modify it in-place.
problem_db: Dict[int, Problem] = {}

def parse_examples_from_question(question_text: str) -> List[TestCase]:
    """
    Finds and parses example blocks from the question text.
    """
    public_cases = []
    
    example_section_match = re.search(r"-----Example-----(.*)", question_text, re.DOTALL)
    if not example_section_match:
        return []

    example_text = example_section_match.group(1)
    
    # Regex looks for "Input" followed by content, then "Output" followed by content
    matches = re.findall(
        r"Input\n(.*?)\nOutput\n(.*?)(?=\n\n|\nInput|\n-----|\Z)", 
        example_text, 
        re.DOTALL
    )

    for inp, outp in matches:
        public_cases.append(
            TestCase(input=inp.strip(), output=outp.strip())
        )
        
    return public_cases


def robust_stringify(data_item: Any) -> str:
    """
    Recursively converts any common data type into a single string 
    for stdin/stdout.
    """
    if isinstance(data_item, str):
        return data_item
    
    if isinstance(data_item, (int, float, bool)):
        return str(data_item)

    if isinstance(data_item, list):
        return "\n".join(map(robust_stringify, data_item))

    if isinstance(data_item, dict):
        try:
            return json.dumps(data_item)
        except Exception:
            return str(data_item)

    if data_item is None:
        return ""
    
    return str(data_item)


def parse_hidden_case_from_io(io_string: str) -> List[TestCase]:
    """
    Parses the 'input_output' JSON string.
    """
    if not io_string or io_string == 'null' or io_string == '"{}"':
        return []
    
    try:
        test_case_data = json.loads(io_string)
        inputs = test_case_data.get('inputs', [])
        outputs = test_case_data.get('outputs', [])
        
        parsed_cases = []

        if inputs and outputs:
            for inp_raw, outp_raw in zip(inputs, outputs):
                
                inp_str = robust_stringify(inp_raw)
                outp_str = robust_stringify(outp_raw)

                if inp_str or outp_str: 
                    parsed_cases.append(
                        TestCase(input=inp_str.strip(), output=outp_str.strip())
                    )
        
        return parsed_cases
            
    except json.JSONDecodeError:
        logger.warning(f"Could not parse 'input_output' field: {io_string[:50]}...")
    except Exception as e:
        raise Exception(f"Error in robust_stringify: {e}")
    
    return []


def load_problems(file_path: str = "problems.jsonl"):
    """
    Loads problems from a .jsonl file into the in-memory problem_db.
    """
    try:
        sys.set_int_max_str_digits(0)
        logger.info("Set sys.set_int_max_str_digits(0) to handle large integers.")
    except Exception as e:
        logger.warning(f"Could not set int_max_str_digits: {e}")

    global problem_db
    logger.info(f"Loading problems from {file_path}...")
    
    temp_db = {}
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                if not line.strip():
                    continue
                
                data = {} 
                try:
                    data = json.loads(line)
                    problem_id = int(data['id'])
                    question_text = data.get('question', '')
                    
                    # --- EXTRACT TITLE LOGIC ---
                    # Use the first line of the question as the title
                    lines = question_text.strip().split('\n')
                    if lines:
                        title = lines[0].strip()
                        # Truncate if it's essentially the whole paragraph
                        if len(title) > 100:
                            title = title[:97] + "..."
                    else:
                        title = f"Problem {problem_id}"
                    # ---------------------------

                    public_cases = parse_examples_from_question(question_text)
                    hidden_cases = parse_hidden_case_from_io(data.get('input_output', '{}'))
                    
                    problem_instance = Problem(
                        id=problem_id,
                        title=title, # Added title
                        question=question_text,
                        difficulty=data.get('difficulty', 'Medium'),
                        public_cases=public_cases,
                        hidden_cases=hidden_cases 
                    )
                    
                    temp_db[problem_id] = problem_instance
                    
                except json.JSONDecodeError:
                    logger.warning(f"Skipping malformed JSON line: {line[:50]}...")
                except Exception as e:
                    logger.error(f"Error processing problem id {data.get('id', 'UNKNOWN')}: {e}")

        # Update the database in-place
        problem_db.clear()
        problem_db.update(temp_db)
        
        logger.info(f"Successfully loaded {len(problem_db)} problems.")
    
    except FileNotFoundError:
        logger.error(f"FATAL: Problem file '{file_path}' not found.")
    except Exception as e:
        logger.error(f"FATAL: Could not load problems: {e}")