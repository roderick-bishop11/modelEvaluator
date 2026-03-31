# Model Evaluator

--- simply put, I just want to run models through a test gauntlet and rank their outputs so that I can choose the best model, for a task possibly at the *per device* level. 


Goals:

1. repeatable testing battery -> input model, output score relative with same set. 
2. reasonable scoring/ranking/stats -> how does one rank a model for what it can do
3. CLI functionality
4. full-fledged solution -> I want all things considered, all parts of a professional project done. 
5. Personal use. I want to personally use this thing for a personal project. 
6. Override-ability -> I want the system to score first, and allow overrides for a human review.
7. definable test sets -> make it easy to define test sets, and run an LLM through them. 