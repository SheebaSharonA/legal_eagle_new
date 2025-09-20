import React, { useState } from "react";
import { Card, Button, Form } from "react-bootstrap";

function LegalChatbot({ docId }) {
  const [messages, setMessages] = useState([
    {
      sender: "bot",
      text: "Hello! Ask me anything about your legal document."
    }
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSend = async () => {
    if (!input.trim()) return;

    const userMessage = { sender: "user", text: input };
    setMessages(prev => [...prev, userMessage]);
    setInput("");
    setLoading(true);

    try {
      // Send question and document text to backend
      const response = await fetch("http://127.0.0.1:5002/query", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({
    query: input,
    doc_id: docId,  // use the stored doc_id
  }),
});


      const data = await response.json();
      const botMessage = { sender: "bot", text: data.answer };
      setMessages(prev => [...prev, botMessage]);
    } catch (err) {
      console.error(err);
      setMessages(prev => [
        ...prev,
        { sender: "bot", text: "Sorry, I couldn't fetch an answer." }
      ]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Card className="shadow-lg border-0 mt-4 p-4">
      <h4>Legal Chatbot</h4>
      <div style={{ maxHeight: "400px", overflowY: "auto", marginBottom: "1rem" }}>
        {messages.map((msg, idx) => (
          <div
            key={idx}
            style={{
              textAlign: msg.sender === "user" ? "right" : "left",
              marginBottom: "0.5rem"
            }}
          >
            <b>{msg.sender === "user" ? "You" : "Legal Eagle"}: </b>
            <span>{msg.text}</span>
          </div>
        ))}
      </div>

      <Form.Control
        type="text"
        placeholder="Ask a question..."
        value={input}
        onChange={(e) => setInput(e.target.value)}
        onKeyDown={(e) => e.key === "Enter" && handleSend()}
        disabled={loading}
      />
      <Button
        variant="primary"
        onClick={handleSend}
        className="mt-2"
        disabled={loading || !input.trim()}
      >
        {loading ? "Fetching answer..." : "Send"}
      </Button>
    </Card>
  );
}

export default LegalChatbot;
