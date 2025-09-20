// src/SummaryChatbotPage.js
import React, { useState, useRef, useEffect } from "react";
import { Upload, FileText, MessageCircle, Sparkles, Download, Globe } from "lucide-react";
import { Container, Card, Button, Form, Modal, Badge, Alert } from "react-bootstrap";
import { useNavigate } from "react-router-dom";
import { auth, db } from "./firebase"; 
import { onAuthStateChanged } from "firebase/auth";
import { signOut } from "firebase/auth";
import axios from "axios";
import LegalChatbot from "./LegalChatbot";



function SummaryChatbotPage() {
  const navigate = useNavigate();
  const [user, setUser] = useState(null);
  const [originalText, setOriginalText] = useState("");

  //otp verification

  const [otpSent, setOtpSent] = useState(false);
const [otp, setOtp] = useState("");
const [otpModalShow, setOtpModalShow] = useState(false);
const [saving, setSaving] = useState(false);


  // Authentication watcher: redirect to login if not signed in
  useEffect(() => {
    const unsubscribe = onAuthStateChanged(auth, (u) => {
      if (!u) {
        navigate("/login");
      } else {
        setUser(u);
      }
    });
    return () => unsubscribe();
  }, [navigate]);

  const handleLogout = async () => {
    try {
      await signOut(auth);
      navigate("/login");
    } catch (err) {
      console.error("Logout failed:", err);
    }
  };

   useEffect(() => {
    // get logged-in user details
    const unsubscribe = onAuthStateChanged(auth, (currentUser) => {
      if (currentUser) {
        setUser(currentUser);
      }
    });
    return () => unsubscribe();
  }, []);

  // --- your existing states ---
  const [uploadedFile, setUploadedFile] = useState(null);
  const [summary, setSummary] = useState("");
  const [isProcessing, setIsProcessing] = useState(false);
  const [showProcessing, setShowProcessing] = useState(false);
  const [selectedLanguage, setSelectedLanguage] = useState("english");
  const [isDragOver, setIsDragOver] = useState(false);
  const fileInputRef = useRef(null);
  const [translatedText, setTranslatedText] = useState("");
  const [loading, setLoading] = useState(false);
  const [docId, setDocId] = useState(null);

  // Chatbot states
  const [messages, setMessages] = useState([
    { sender: "bot", text: "Hello! Upload a document and I'll help you understand it better. Ask me anything about your legal documents!" },
  ]);
  const [input, setInput] = useState("");

  // ... (keep your handleFileUpload, drag handlers, handleProcessPdf, handleSend etc.)
  // For brevity I'll reuse the fetch-based backend handler you already have:

  const handleFileUpload = (file) => {
    if (file && file.type === "application/pdf") {
      setUploadedFile(file);
      setSummary("");
    } else {
      alert("Please upload a PDF file only.");
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragOver(false);
    const files = Array.from(e.dataTransfer.files);
    if (files.length > 0) handleFileUpload(files[0]);
  };

  const handleDragOver = (e) => { e.preventDefault(); setIsDragOver(true); };
  const handleDragLeave = (e) => { e.preventDefault(); setIsDragOver(false); };

  const handleProcessPdf = async () => {
    if (!uploadedFile) {
      alert("Please upload a PDF first.");
      return;
    }
    setIsProcessing(true);
    setShowProcessing(true);
    try {
      const formData = new FormData();
      formData.append("file", uploadedFile);
      const response = await fetch("http://127.0.0.1:5000/process_pdf", {
        method: "POST",
        body: formData,
      });
      if (!response.ok) throw new Error("Failed to process PDF");
      const data = await response.json();
      setSummary(data.summary);
      // store original text too
      setOriginalText(data.text);

        // 2. Call chatbot API with the extracted text
    const chatbotResponse = await fetch("http://127.0.0.1:5002/process_pdf_chatbot", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text: data.text }),
    });

    if (!chatbotResponse.ok) throw new Error("Failed to process PDF for chatbot");
    const chatbotData = await chatbotResponse.json();

    // Save doc_id for later queries
    setDocId(chatbotData.doc_id);
      setMessages(prev => [...prev, { sender: "bot", text: `I've successfully analyzed "${uploadedFile.name}". You can now ask me specific questions about its contents!` }]);
    } catch (err) {
      console.error(err);
      alert("Error processing PDF: " + err.message);
    } finally {
      setIsProcessing(false);
      setShowProcessing(false);
    }
  };


const handleSaveDocument = async () => {
  if (!user) {
    alert("Please log in to save your document.");
    return;
  }

  if (!summary || !originalText) {
    alert("No document summary available to save.");
    return;
  }

  try {
    // Request OTP from backend
    const res = await fetch("http://127.0.0.1:5000/request_otp", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email: user.email }),
    });

    const data = await res.json();
    if (res.ok) {
      setOtpSent(true);
      setOtpModalShow(true);
      alert(data.message);
    } else {
      alert(data.error || "Failed to send OTP");
    }
  } catch (err) {
    console.error(err);
    alert("Error requesting OTP: " + err.message);
  }
};

 // Translate summary
  // Translate summary
const handleTranslate = async (text, targetLang) => {
  if (!text || !targetLang) return;
  setLoading(true);
  setTranslatedText("");

  console.log("Text to translate:", text);
  console.log("Target language:", targetLang);

  try {
    const response = await axios.post("http://127.0.0.1:5001/translate", {
      text: text,             // The text to translate
      target_lang: targetLang // Matches backend key exactly
    });

    console.log("Translation response:", response.data);

    if (response.data.translated_text) {
      setTranslatedText(response.data.translated_text);
    } else {
      console.warn("No translated_text returned from backend.");
    }
  } catch (err) {
    console.error(err);
    alert("Translation failed. See console for details.");
  } finally {
    setLoading(false);
  }
};



const handleVerifyOtp = async () => {
  if (!otp.trim()) return;

  setSaving(true);
  try {
    const res = await fetch("http://127.0.0.1:5000/verify_otp", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email: user.email, otp }),
    });

    const data = await res.json();
    if (res.ok) {
      alert(data.message);

      // Now save document to Firestore
      const idToken = await user.getIdToken(); // get Firebase auth token
      const saveRes = await fetch("http://127.0.0.1:5000/save_document", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          idToken,
          fileName: uploadedFile?.name || "unknown.pdf",
          summary,
          fullText: originalText
        }),
      });

      const saveData = await saveRes.json();
      if (saveRes.ok) {
        alert(saveData.message);
      
      } else {
        alert(saveData.error || "Failed to save document");
      }

      setOtpModalShow(false);
      setOtp(""); // reset
      setOtpSent(false);
    } else {
      alert(data.error || "OTP verification failed");
    }
  } catch (err) {
    console.error(err);
    alert("Error verifying OTP: " + err.message);
  } finally {
    setSaving(false);
  }
};

  

  const languages = [
    { code: "english", name: "English", flag: "🇺🇸" },
    { code: "tamil", name: "தமிழ்", flag: "🇮🇳" },
    { code: "hindi", name: "हिंदी", flag: "🇮🇳" },
    { code: "spanish", name: "Español", flag: "🇪🇸" },
    { code: "french", name: "Français", flag: "🇫🇷" }
  ];

  const headerStyle = {
    background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
    color: 'white',
    position: 'relative', // important so top-left greeting can be positioned
    overflow: 'hidden'
  };

  // compute display name fallback
  const displayName = user?.displayName || (user?.email ? user.email.split("@")[0] : "User");

  // --- JSX (I kept your original layout and simply added top-left greeting + Logout) ---
  return (
    <div style={{ minHeight: '100vh', background: 'linear-gradient(135deg, #f0f9ff 0%, #faf5ff 100%)' }}>
      {/* Header */}
      <div style={headerStyle} className="py-5">
        {/* TOP-LEFT greeting / logout */}
        <div style={{ position: "absolute", left: 20, top: 18, zIndex: 50 }}>
          <div className="d-flex align-items-center gap-2">
            <div style={{ color: "white", fontWeight: 600 }}>Hello, {displayName}</div>
            <Button variant="light" size="sm" onClick={handleLogout}>Logout</Button>
          </div>
        </div>

        <div style={{ position: 'absolute', inset: 0, background: 'rgba(0,0,0,0.1)' }}></div>
        <Container className="text-center position-relative">
          <div className="mb-4 d-inline-flex align-items-center justify-content-center" 
               style={{ width: '80px', height: '80px', background: 'rgba(255,255,255,0.2)', borderRadius: '50%', backdropFilter: 'blur(10px)' }}>
            <Sparkles size={40} color="white" />
          </div>
          <h1 className="display-3 fw-bold mb-3" style={{ background: 'linear-gradient(135deg, #ffffff 0%, #e0e7ff 100%)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>
            Legal Eagle AI
          </h1>
          <p className="lead" style={{ color: '#e0e7ff', maxWidth: '600px', margin: '0 auto' }}>
            Transform legal documents with AI-powered analysis, translation, and intelligent chat assistance
          </p>
        </Container>
      </div>

      {/* Rest of your UI (upload card, chatbot etc.) — unchanged except we kept handlers */}
      <Container className="py-5">
        {/* Document Upload Section */}
        <Card className="shadow-lg border-0 mb-4" style={{ borderRadius: '1rem', overflow: 'hidden' }}>
          {/* ... keep the same Card header and body as before ... */}
          <div style={{ background: 'linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%)', color: 'white', borderRadius: '0.5rem 0.5rem 0 0' }} className="p-4">
            <div className="d-flex align-items-center">
              <FileText size={28} className="me-3" />
              <div>
                <h2 className="h3 mb-1 fw-bold">Document Analyzer</h2>
                <p className="mb-0 opacity-75">Upload your PDF and get instant AI-powered insights</p>
              </div>
            </div>
          </div>

          <Card.Body className="p-4">
            {/* Upload area (use your existing JSX) */}
            <div
              style={{
                border: `2px dashed ${isDragOver ? '#3b82f6' : uploadedFile ? '#10b981' : '#d1d5db'}`,
                borderRadius: '0.75rem',
                padding: '3rem',
                textAlign: 'center',
                cursor: 'pointer',
                transition: 'all 0.3s ease',
                backgroundColor: isDragOver ? '#eff6ff' : uploadedFile ? '#f0fdf4' : '#f8fafc'
              }}
              onDrop={handleDrop}
              onDragOver={handleDragOver}
              onDragLeave={handleDragLeave}
              onClick={() => fileInputRef.current?.click()}
            >
              <input
                ref={fileInputRef}
                type="file"
                accept=".pdf"
                onChange={(e) => { if (e.target.files[0]) handleFileUpload(e.target.files[0]); }}
                className="d-none"
              />
              {uploadedFile ? (
                <div>
                  <h4 className="fw-semibold">{uploadedFile.name}</h4>
                  <p>{(uploadedFile.size / 1024 / 1024).toFixed(2)} MB • Ready to process</p>
                </div>
              ) : (
                <div>
                  <h4>Drop your PDF here or click to browse</h4>
                </div>
              )}
            </div>

            {uploadedFile && (
              <div className="text-center mt-4">
                <Button onClick={handleProcessPdf} disabled={isProcessing} size="lg">
                  {isProcessing ? "Processing..." : "Analyze Document"}
                </Button>
              </div>
            )}

            {/* summary display */}
      {summary && (
        <div className="mt-3 p-3 border rounded bg-light">
          <h5>Summary</h5>
          <p>{summary}</p>
          {/* Save button */}
          <Button variant="success" onClick={handleSaveDocument} className="mt-3">
            Save Document
          </Button>
           {/* Language Dropdown */}
          <select
            className="form-select d-inline-block w-auto mt-3 me-2"
            value={selectedLanguage}
            onChange={(e) => setSelectedLanguage(e.target.value)}
          >
            <option value="">Select Language</option>
            <option value="hi">Hindi</option>
            <option value="ta">Tamil</option>
            <option value="te">Telugu</option>
            <option value="ml">Malayalam</option>
            <option value="kn">Kannada</option>
          </select>

          {/* Translate Button */}
          <Button
            variant="primary"
            onClick={() => { console.log("Translate clicked!"); handleTranslate(summary, selectedLanguage); }}
            className="mt-3"
            disabled={!selectedLanguage || loading}
          >
            {loading ? "Translating..." : "Translate"}
          </Button>
           {/* Display translated text */}
      {translatedText && (
        <div className="mt-3 p-3 border rounded bg-light">
          <h5>Translated Text</h5>
          <p>{translatedText}</p>
        </div>
      )}
        </div>
        
      )}

      <Modal show={otpModalShow} onHide={() => setOtpModalShow(false)} centered>
  <Modal.Header closeButton>
    <Modal.Title>Enter OTP</Modal.Title>
  </Modal.Header>
  <Modal.Body>
    <Form.Control
      type="text"
      placeholder="Enter OTP"
      value={otp}
      onChange={(e) => setOtp(e.target.value)}
    />
  </Modal.Body>
  <Modal.Footer>
    <Button variant="secondary" onClick={() => setOtpModalShow(false)}>
      Cancel
    </Button>
    <Button variant="primary" onClick={handleVerifyOtp} disabled={saving}>
      {saving ? "Verifying..." : "Verify OTP"}
    </Button>
  </Modal.Footer>
</Modal>

          </Card.Body>
        </Card>

        {/* Chatbot Section */}
{docId && <LegalChatbot docId={docId} />}


      </Container>

      {/* Processing Modal */}
      <Modal show={showProcessing} onHide={() => setShowProcessing(false)} centered backdrop="static">
        <Modal.Body className="text-center p-5">
          <div className="mb-4 d-inline-flex align-items-center justify-content-center" style={{ width: '64px', height: '64px', background: '#dbeafe', borderRadius: '50%' }}>
            <div className="spinner-border text-primary" role="status"></div>
          </div>
          <h3 className="h4 fw-semibold text-dark mb-2">Analyzing Document</h3>
          <p className="text-muted mb-4">Our AI is processing your PDF and extracting key insights...</p>
        </Modal.Body>
      </Modal>
    </div>
  );
}

export default SummaryChatbotPage;
