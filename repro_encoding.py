import json
from pydantic import BaseModel

class Track(BaseModel):
    id: str
    path: str

# Create a string with surrogates (invalid UTF-8 sequence in Python string)
# \udce5 is a surrogate often used for invalid bytes
surrogate_str = "test_\udce5_file"

t = Track(id="1", path=surrogate_str)

print(f"Track path: {repr(t.path)}")

# Simulate FastAPI response model exclude
try:
    dump = t.model_dump(exclude={"path"})
    print(f"Dump (exclude path): {dump}")
    
    json_output = json.dumps(dump)
    print(f"JSON Output: {json_output}")
except Exception as e:
    print(f"Error during dump/json: {e}")

# Try without exclude to see it fail
try:
    dump_full = t.model_dump()
    print(f"Dump (full): {dump_full}")
    json.dumps(dump_full)
except Exception as e:
    print(f"Error during full dump json: {e}")
