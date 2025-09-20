import { BrowserRouter as Router, Routes, Route } from "react-router-dom";

import SummaryChatbotPage from "./SummaryChatbotPage";
import Login from "./components/Login";
import Signup from "./components/Signup";

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<Login />} />
        <Route path="/login" element={<Login />} />
        <Route path="/signup" element={<Signup />} />
        <Route path="/main" element={<SummaryChatbotPage />} />
      </Routes>
    </Router>
  );
}

export default App;
