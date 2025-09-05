import React, { useState, useEffect, useRef } from "react";
  import "./chatPrompt.css";
  import FileUpload from "./FileUpload";
  import AiChat from "./aiChat";
  import Courses from "./courses";
  import Account from "./account";


  function ChatPrompt({goDashboard, initialView = "chat"}) {
    const [messages, setMessages] = useState([]);
    const [input, setInput] = useState("");
    const [uploadingId, setUploadingId] = useState(null);
    const boxRef = useRef(null);
    const [studentData, setStudentData] = useState(null);
    const [activeView, setActiveView] = useState(initialView); 
  // can be "chat" or "upload"

    useEffect(() => {
      const loggedInId = localStorage.getItem("studentId"); // save this in login
      if (loggedInId) {
        fetch(`http://localhost:5000/student/${loggedInId}`)
          .then((res) => res.json())
          .then((data) => {
            console.log("Fetched student data:", data);
            if (!data.error) {
              setStudentData(data); // store decrypted data
            }
          })
          .catch((err) => console.error("Error fetching student:", err));
      } else {
        setStudentData(null); // Clear student data if no studentId found
      }
    }, []);

    // Debugging: log studentData every time it changes
    useEffect(() => {
      console.log("studentData state:", studentData);
    }, [studentData]);

    // If initialView changes while ChatPrompt is mounted, update activeView
    useEffect(() => {
      setActiveView(initialView);
    }, [initialView]);



    const sendMessage = (text) => {
      // Add user's message
      setMessages((prev) => [...prev, { sender: "user", text }]);

      const isScheduleRequest = text.toLowerCase().includes("schedule");
      const isRecordRequest = text.toLowerCase().includes("record");


      const loadingMsg = { sender: "bot", text: "Thinking...", type: "loading" };
      setMessages((prev) => [...prev, loadingMsg])

      // Call Flask backend
      fetch("http://localhost:5000/chatprompt", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query: text }),
      })
        .then((res) => res.json())
        .then((data) => {
          setMessages((prev) => {
            const filtered = prev.filter((msg) => msg.type !== "loading");
            return [
              ...filtered,
              {
                sender: "bot",
                text: data.response || "No Response From the AI",
                type: isScheduleRequest ? "schedule" : "defaultRes",
                type: isScheduleRequest ? "schedule" : "defaultRes",
              },
            ];
          });
      })
        .catch(() => {
          setMessages((prev) => [
            ...prev,
            {
              sender: "bot",
              text: "Sorry, there was an error connecting to the AI.",
              type: "defaultRes",
            },
          ]);
        });
    };

    // Handle form submission
    const handleSubmit = (e) => {
      // Prevents the page from reloading everytime na mag susubmit ng new message
      e.preventDefault();
      if (input.trim() === "") return;

      sendMessage(input);
      setInput("");
    };

    // when a file is selected in FileUpload
    const handleFileSelect = (file, result) => {
      console.log("File uploaded:", file.name, result.message);
    };

    // Scroll to the bottom of the chat box when messages change
    useEffect(() => {
      if (boxRef.current) {
        boxRef.current.scrollTop = boxRef.current.scrollHeight;
      }
    }, [messages]);

    return (
      <div className="chat-prompt w-full h-full p-0 m-0">
        <div className="mainContent flex h-full justify-center items-center">
          {/* NavBar */}
          <div className="navBar w-full h-full flex flex-col bg-[#792C1A] justify-around z-10">
            
            <div className="flex flex-col h-full justify-between gap-5 px-[8%] py-7">
            
              <div className="w-full h-fit flex flex-col gap-4">
                <div className="flex gap-[2%] items-center">
                    <button onClick={goDashboard} className="nav w-auto !py-4">
                      <img
                        src="./public/images/PDM-Logo.svg"
                        alt="PDM-LOGO"
                        className="navBtn w-[6vw] aspect-square"
                      />
                    </button>
                  <h1 className="text-[#ffffff] font-sans text-[clamp(1rem,3vw,4rem)] font-bold">
                    PDM
                  </h1>
                </div>
                <div className="w-full rounded-2xl h-1 bg-gray-400" ></div>

                <div onClick={() => setActiveView("chat")} className="w-full  flex items-center h-[5vh] hover:scale-103 transition-all duration-300 cursor-pointer">
                  <button href="/chat" onClick={() => setActiveView("chat")}>
                    <img src="/navIco/chatBox.svg" alt="" className="w-[80%] aspect-square cursor-pointer"/>
                  </button>
                  <h1 className="text-white self-center text-[clamp(1rem,1.2vw,1.5rem)] ">Smart System</h1>
                </div>
                
                {/* Loaded Files: Hide for student/guest */}
                {(studentData?.role !== "student" && studentData?.role !== "guest") && (
                  <div onClick={() => setActiveView("upload")} className="w-full flex items-center h-[5vh] hover:scale-103 transition-all duration-300 cursor-pointer">
                    <button href="/files" onClick={() => setActiveView("upload")}>
                      <img src="/navIco/loadedFiles.svg" alt="" className="w-[80%] aspect-square cursor-pointer"/>
                    </button>
                    <h1 className="text-white text-[clamp(1rem,1.2vw,1.5rem)] ">Loaded Files</h1>
                  </div>
                )}

                {/* Programs: Hide for student/guest/faculty */}
                {(studentData?.role !== "student" && studentData?.role !== "guest" && studentData?.role !== "faculty") && (
                  <div onClick={() => setActiveView("courses")} className="w-full flex items-center h-[5vh] hover:scale-103 transition-all duration-300 cursor-pointer">
                    <button onClick={() => setActiveView("courses")} href="/files" >
                      <img src="/navIco/programs.svg" alt="" className="w-[80%] aspect-square cursor-pointer"/>
                    </button>
                    <h1 className="text-white text-[clamp(1rem,1.2vw,1.5rem)] ">Programs</h1>
                  </div>
                )}
                
              </div>

              <div className="w-full h-fit flex flex-col gap-4">
                <div className="w-full rounded-2xl h-1 bg-gray-400" ></div>

                <div onClick={() => setActiveView("account")} className="w-full flex items-center h-[5vh] hover:scale-103 transition-all duration-300 cursor-pointer">
                  <button href="/files" onClick={() => setActiveView("account")}>
                    <img src="/navIco/user.svg" alt="" className="w-[80%] aspect-square cursor-pointer"/>
                  </button>
                  <h1 className="text-white text-[clamp(1rem,1.2vw,1.5rem)] ">Account</h1>
                </div>

                
                </div>
            </div>
          </div>

          {/* CHAT BOX */}
          <div className="main flex flex-col gap-2 justify-center items-center w-full h-screen">
          <div className={`${activeView === "chat" ? "flex" : "hidden"} w-full h-full justify-center items-center`}>
              <AiChat studentData={studentData}
                messages={messages}
                input={input}
                setInput={setInput}
                handleSubmit={handleSubmit}
                boxRef={boxRef}
              />  
            </div>

            <div className={`${activeView === "upload" ? "flex" : "hidden"} w-full h-full justify-center items-center`}>
              <FileUpload studentData={studentData} onFileUpload={handleFileSelect} />
            </div>

            <div className={`${activeView === "courses" ? "flex" : "hidden"} w-full h-full justify-center items-center`}>
              <Courses studentData={studentData}/>
            </div>

            <div className={`${activeView === "account" ? "flex" : "hidden"} w-full h-full justify-center items-center`}>
              <Account studentData={studentData} />
            </div>
            

          
          </div>
        </div>
      </div>
    );
  }
  export default ChatPrompt;
