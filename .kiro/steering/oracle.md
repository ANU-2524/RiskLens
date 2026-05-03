# Oracle — Agent Steering Rules

## Code style
- Python: PEP8, type hints on all functions, docstrings on all public methods
- TypeScript: strict mode enabled, no `any` types, named exports only
- All async Python functions must use `async/await` with proper error handling
- Never hardcode secrets, API keys, or connection strings

## Architecture rules
- All database access goes through SQLAlchemy ORM — no raw SQL
- All external API calls wrapped in retry logic with exponential backoff
- Redis cache TTL: 5 minutes for risk scores, 1 minute for live alerts
- All new API routes must have a corresponding pytest test

## AI integration rules
- Claude API calls must always include a system prompt establishing the Oracle context
- All AI-generated content stored with the prompt used to generate it (audit trail)
- Token budget per Claude call: max 2000 output tokens
- Rate limit Claude calls: max 50/hour to control costs

## Frontend rules
- All colors from the defined cosmic palette only — no arbitrary hex values
- Three.js scene must not exceed 60MB GPU memory
- All API calls use React Query — no raw fetch() in components
- Mobile breakpoint at 768px: galaxy map replaced with card grid
