require('dotenv').config();
const express = require('express');
const bodyParser = require('body-parser');
const { Configuration, OpenAIApi } = require('openai');

const { initPinecone } = require('./services/chroma');
const { ingestDocument } = require('./services/ingestDocument');
const { fetchGDriveDocuments } = require('./services/gdrive');
const { crawlWebsite } = require('./services/crawl');
const { embedTextChunk } = require('./services/embed');

const app = express();
app.use(bodyParser.json());

const openai = new OpenAIApi(new Configuration({
  apiKey: process.env.OPENAI_API_KEY
}));

// 1) SYNC Endpoint
app.post('/sync', async (req, res) => {
  try {
    // (A) Website Crawl (placeholder)
    // Add your real URLs
    const urlsToCrawl = [
      'https://www.neckarmedia.com/',
      'https://www.neckarmedia.com/referenzen/',

    ];
    for (let url of urlsToCrawl) {
      const textContent = await crawlWebsite(url);
      // Construct a doc object
      const docObj = {
        fileId: url, // or "website-page-about"
        title: `Website Page: ${url}`,
        textContent
      };
      await ingestDocument(docObj);
    }

    // (B) G-Drive Docs
    const driveDocs = await fetchGDriveDocuments();
    for (let doc of driveDocs) {
      // doc = { fileId, title, textContent }
      await ingestDocument(doc);
    }

    return res.json({ message: 'Sync completed successfully.' });
  } catch (error) {
    console.error(error);
    return res.status(500).json({ error: 'Sync failed.' });
  }
});

// 2) ASK Endpoint
app.post('/ask', async (req, res) => {
  try {
    const { query } = req.body; // user question

    // (A) Embed the query
    const queryEmbedding = await embedTextChunk(query);

    // (B) Search Pinecone for relevant chunks
    const index = await initPinecone();
    const topK = 3; // number of relevant chunks to retrieve
    const pineconeQuery = {
      vector: queryEmbedding,
      topK,
      includeMetadata: true
    };
    const searchResponse = await index.query({ queryRequest: pineconeQuery });
    const matches = searchResponse.matches || [];

    // (C) Construct a context from retrieved chunks
    let contextText = '';
    matches.forEach((match, i) => {
      const metadata = match.metadata || {};
      contextText += `\nChunk #${i+1} (score: ${match.score}): ${metadata.text}\nSource: ${metadata.source}\n`;
    });

    // (D) Call OpenAI Chat with the retrieved context
    const systemMessage = `
      You are a helpful assistant. Use the provided context to answer the user's question.
      If the context is not sufficient, say you don't have enough info.
    `;

    const userMessage = `
      Context:
      ${contextText}

      Question: ${query}
    `;

    const chatResponse = await openai.createChatCompletion({
      model: 'gpt-3.5-turbo',
      messages: [
        { role: 'system', content: systemMessage },
        { role: 'user', content: userMessage }
      ],
      max_tokens: 300
    });

    const answer = chatResponse.data.choices[0].message.content.trim();

    // Return a structured response
    return res.json({
      answer,
      references: matches.map(m => ({
        source: m.metadata.source,
        score: m.score
      }))
    });
  } catch (error) {
    console.error(error);
    return res.status(500).json({ error: 'Error processing query.' });
  }
});

// Start the server
const PORT = process.env.PORT || 3000;
app.listen(PORT, async () => {
  await initPinecone(); // Ensure Pinecone is initialized
  console.log(`RAG bot server listening on port ${PORT}`);
});
