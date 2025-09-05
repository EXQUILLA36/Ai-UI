import React, { useState, useEffect, useRef } from "react";
import "./chatPrompt.css";
import ReactMarkdown from "react-markdown";
import TypewriterText from './TypeWriter.jsx';

function AiChat({ messages, input, setInput, handleSubmit, boxRef, studentData }) {
  useEffect(() => {
    console.log("AiChat mounted");
    return () => console.log("AiChat unmounted");
  }, []);
  return (
    <>
      <div className='w-full h-full flex flex-col items-center justify-between py-5 mr-2'>
        {/* Header for Chat Box */}
      <div className=" w-full h-[10%] flex flex-col gap-2 items-center">
        <div className='flex justify-between w-[90%]'> 
            <div className='flex items-center'>
            <div className="bg-[url('/navIco/iconAI.svg')] bg-contain bg-no-repeat w-[3vw] aspect-square"></div>
                <h1 className="text-[clamp(1.3rem,1.2vw,1.8rem)] font-sans font-medium">Intelligent System</h1>
            </div>
            <div className='flex gap-2 items-center'>
                <h1 className="text-[clamp(1.3rem,1.2vw,1.8rem)] font-sans font-medium">
                  {studentData ? `${studentData.firstName} ${studentData.lastName}` : "User Account"}
                </h1>
                <div className="bg-[url('/navIco/profile-circle.svg')] bg-contain bg-no-repeat w-[3vw] aspect-square"></div>
            </div>
        </div>
        <div className='w-[90%] h-1 rounded-2xl bg-gray-500'></div>
      </div>
      {/* Main Chat Box */}
      <div className="chatBox flex flex-col justify-between items-center w-[95%] h-[85%] rounded-lg !p-4">
        {/* Displays the message and response  */}
        <div
          ref={boxRef}
          className="box relative flex flex-col w-[90%] h-[90%] gap-4 overflow-y-auto p-4 rounded-lg"
        >
          {messages
            .filter(msg => msg.type !== "uploading" && msg.type !== "uploaded")
            .map((msg, i) => {
              const isBotResponse = msg.sender === "bot" && msg.type !== "loading";
              const isLastMessage = i === messages.length - 1;

              return (
                <div
                  key={i}
                  className={`content p-2 rounded-lg max-w-[90%] ${
                    msg.type === "userUpload"
                      ? "bg-amber-600 userUploaded self-end !rounded-sm"
                      : msg.sender === "user"
                      ? "bg-amber-600 userRespo self-end !rounded-sm"
                      : msg.type === "schedule"
                      ? "bg-amber-100 border border-gray-400 self-start text-sm whitespace-pre-wrap"
                      : msg.type === "lists"
                      ? "bg-amber-100 border border-gray-400 self-start text-sm whitespace-pre-wrap"
                      : msg.type === "loading"
                      ? "bg-gray-600/50 w-20 self-start !rounded-sm"
                      : "bg-amber-200 botRespo self-start break-words !rounded-sm"
                  }`}
                >
                  {msg.type === "loading" ? (
                    <div className="flex gap-1 w-full items-center">
                      <span className="chatLoader"></span>
                    </div>
                  ) : (
                    msg.text
                  )}
                </div>
              );
            })}




        </div>

        <div className="searchBox component w-[90%] h-[8%] !mt-4 pr-5 bg-gray-50 flex justify-center items-center">
          <form
            onSubmit={handleSubmit}
            className="w-full h-full flex justify-center items-center"
          >
            <input
              type="text"
              placeholder="Ask anything..."
              value={input}
              onChange={(e) => setInput(e.target.value)}
              className="w-full h-full !p-4 font-sans text-2xl focus:outline-none focus:ring-0"
            />
            <button className="send w-auto !py-4" />
            <img
              src="./navIco/send.svg"
              alt="Send"
              className="send w-[5%] aspect-square cursor-pointer transition-transform duration-300 hover:translate-x-2"
              onClick={handleSubmit}
            />
            <button />
          </form>
        </div>
      </div>
      </div>
    </>
  );
}

export default AiChat;