# Extraction Pipeline — Post Mortem

## What worked
- Our extraction proved to be mostly succesful. All of our fields gave expected results with a few exceptions. We added extraction_notes and confidence score as an outlet for model misalignment/edge cases. 

## Failure modes discovered
- Several shortcomings occurred. The first being the mishandling of various currencies for the salary. We initially had the salaray fields min_usd, max_usd, which implied a currency type and ultimately lead to implicit conversions by the LLM due to our error. This was not intended and instead we expanded the model to allow for any currency. 

Another issue was a lack of feedback on the LLM's perceived performance. Although it did coorelate with what we'd expect, the coefficient wasn't as large as we'd like and if we're scaling this we'd need to have a precise agreement on what's properly fitting into the model and what isn't (hopefully factoring out some of the LLMS implicit conversions that we'd rather like to be logged as notes for future model changes)

## Schema decisions and why
- Overall the schema is pretty fair for a software development position. The roles are fairly standard with an unknown bucket. Work location similarly well defined. The salaray was modified to be currency agnostic, this is likely fine but could still be some hourly/monthly wages that could have conversion issues that we may want to be aware of. 
JobPosting could certainly be refined in tandom with our system prompt. We'd likely want to add a bit more precision to the confidence score, detailing to the LLM a bit more of how we expect them to score. The location could be modified as well if we're interested in more details, we'd create a new class with the corresponding fields for that (address, country, state/province).

## What I'd change at 10x scale
- We'd like to have a more refined prompt, enabling a more robust confidence scoring system that attempts to retain some of the implicit coverups the LLM does which would otherwise detract from the score. We'd also give it some context for various unceartainty scores would actually correspond to in a more precise sense than being left to its own devices. Looking at several more job postings to see how we could avoid any potetnial undiscovered model ambiguities. For notes we can have the LLM suggest new fields or changes as well. 

A proper API error handler is needed as well 

## Open questions
- None at the moment, still digesting the whole process, but would like to revise this with you then push forward as learning on the job is a great way to learn. 