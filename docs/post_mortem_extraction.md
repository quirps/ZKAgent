# Extraction Pipeline — Post Mortem

## What worked
- Our extraction proved to be mostly succesful. All of our fields gave expected results with a few exceptions. We added extraction_notes and confidence score as an outlet for model misalignment/edge cases. 

## Failure modes discovered
- Several shortcomings occurred. The first being the mishandling of various currencies for the salary. We initially had the salaray fields min_usd, max_usd, which implied a currency type and ultimately lead to implicit conversions by the LLM due to our error

## Schema decisions and why
- ...

## What I'd change at 10x scale
- ...

## Open questions
- ...