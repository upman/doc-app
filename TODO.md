TODO

- Multiple documents support - Currently, the app only supports sending one document along with multiple questions.
- Processing pipeline in a separate process listening to a queue - To make the processing more robust and fault tolerant, the processing requests should get put in a queue or in the database and a separate process should pick these up.
- Use a file store like s3 -- Currently the uploaded files are just thrown onto the file system.
    - Files get overwritten
- Better context management. -- Currently the whole document is just thrown in the context.
I would do some chunking and run prompts in parallel and then combine the results. Maybe multiple runs to improve recall.
- The app doesn't extract the exact location where the information was present in the doc currently. I was thinking of using Langextract, but didn't have enough time to think how to get question answering working on top it's architecture.
- Language support. Outputs are all in english. Need German output or a way to specify it.

