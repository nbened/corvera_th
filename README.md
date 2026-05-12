# Run this MCP

1. `uv pip install -r requirements.txt`
2. Create `.env` with `ERP_API_KEY=trial_...`
3. Place EPOS CSVs in `epos/`
4. Connect from any MCP client (Claude Desktop config below):
5. Run `open ~/Library/Application\ Support/Claude/claude_desktop_config.json` in terminal, then add below:
                                                                

```json
{
  "mcpServers": {
    "verdano-ops": {
      "command": "uv",
      "args": ["run", "python", "main.py"],
      "cwd": "/path/to/corvera_takehome"
    }
  }
}
```


# Adding a new retailer (2-200)

All RESTful APIs are type-safe and abstracted. Literally just create a folder in retailers to onboard a new one.

1. Create `controllers/retailer/<name>/` with two files, following the pattern already present. The `model` file is essentially your csv schema, the `__init__` file is an abstracted controller to have useful code around it
2. Drop the CSVs in `epos/` following the naming convention `<name>_*forecast*.csv` and `<name>_*actuals*.csv`.

Done. No edits to FulfillmentController, main.py, or anywhere else. The controller auto-discovers the new retailer from the folder name at startup.


# Adding a new deterministic check

The agent by 

Each pipeline step is (line) → line.

1. Add a method on FulfillmentController. Signature is `attach_<thing>(self, line: FulfillmentLine) -> FulfillmentLine`. Assign fields directly on the line and return it.
2. Optionally add a field to FulfillmentLine with a None default so existing flows don't break.
3. Insert the step into evaluate_row between the appropriate existing steps. Order matters only when one check depends on another's output.
4. If the check can block, add a new value to the BlockReason Literal and emit it from classify (not from attach_*). Keep status decisions in one method.


# BONUS: Adding a new ERP

Not completely supported the way retailers are, but the path is the same — repeat the Verdano pattern.

1. Create `controllers/erp/<provider>/` mirroring `controllers/erp/verdano/`. 
2. Register in `controllers/erp/__init__.py` — add to `_REGISTRY` mapping provider name to controller class.
3. Call from main.py with `ERPController(erp="<provider>")` to get the new instance.

Step 1 is the one-time protocol extraction. Steps 2–5 are per-provider.

# Demo
Hit our verdano tool and answer the following: 
What can we fulfill next week, what is at risk, and what needs human review?
Make sure to show the data from the first tool call in a table and the data from the data input into the second tool call in a table as well