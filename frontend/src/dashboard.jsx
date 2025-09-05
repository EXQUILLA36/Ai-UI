import { use, useEffect, useState } from "react";
import "./dashboard.css";
import CreatingAccount from "./creatingAccount.jsx";
import UsingApp from "./usingApp.jsx";
import NavigatingApp from "./navigatingApp.jsx";
import CourseDisplay from "./courseDisplay.jsx";

function Dashboard({goChat, goAccounts,goLogin}) {
   const [activeIndex, setActiveIndex] = useState(1);
   const [activeView, setActiveView] = useState(1); 
   const [scrollPage, setScrollPage] = useState("home")

   useEffect(() => {
    if (!scrollPage) return;

    const target = document.getElementById(scrollPage);
    if (!target) return;

    const offset = 80;
    const elementPosition = target.getBoundingClientRect().top + window.scrollY;
    const offsetPosition = elementPosition - offset;

    const start = window.scrollY;
    const distance = offsetPosition - start;
    const duration = 300;
    let startTime = null;

    function animation(currentTime) {
      if (startTime === null) startTime = currentTime;
      const timeElapsed = currentTime - startTime;
      const progress = Math.min(timeElapsed / duration, 1);

      window.scrollTo(0, start + distance * progress);

      if (timeElapsed < duration) requestAnimationFrame(animation);
    }

    requestAnimationFrame(animation);
    setScrollPage("");
  }, [scrollPage]);

  const buttons = [
    {
     id: 0,
      title: "Creating Account",
      subtitle: "Register and Login Your Account",
      defaultImg: "/dashboardBtn/btn1Act.svg",
      activeImg: "/dashboardBtn/btn1Una.svg",
    },
    { 
      id: 1,
      title: "Using the System",
      subtitle: "Utilizig Smart System for your needs",
      defaultImg: "/dashboardBtn/btn2Act.svg",
      activeImg: "/dashboardBtn/btn2Una.svg",
    },
    { 
      id: 2,
      title: "Navigating the App",
      subtitle: "Going through each features",
      defaultImg: "/dashboardBtn/btn3Act.svg",
      activeImg: "/dashboardBtn/btn3Una.svg",
     },
  ];

  const handleLogout = () => {
    localStorage.removeItem("studentId"); // clear saved session
    goLogin(); // go back to Login page
  };
  return (
    <>
    <div className="flex flex-col">
      <div className="w-full h-fit py-2 flex flex-col bg-white items-center fixed border-b-12 border-[#FFDB0D] z-10">
        <div className="w-full h-full flex justify-between px-4 items-center">
          <div className=" flex gap-8 text-[clamp(0.5rem,1.2vw,1.2rem)] font-medium">
            <a
              href="#Home"
              onClick={(e) => {
                e.preventDefault();
                setScrollPage("home");
              }}
            >
              Home
            </a>
            <a
              href="#Programs"
              onClick={(e) => {
                e.preventDefault();
                setScrollPage("programs");
              }}
            >
              Programs
            </a>
            <a
              href="#About"
              onClick={(e) => {
                e.preventDefault();
                setScrollPage("about");
              }}
            >
              About Pdm
            </a>
          </div>

          <div className="bg-[url('/images/PDM-Logo.svg')] bg-contain bg-center bg-no-repeat w-[4%] aspect-square"></div>

          <div className="flex flex-row gap-2 h-12">
            <div className="flex items-center gap-8 text-[clamp(0.5rem,1.2vw,1.2rem)] h-full font-medium">
              <button onClick={handleLogout} className="cursor-pointer hover:underline">
                  Log Out
                </button>
              <a onClick={goAccounts} className="cursor-pointer hover:underline">Accounts</a> 
            </div>
            <div className="bg-[url('/navIco/profile-circle.png')] bg-contain bg-center bg-no-repeat w-[20%] aspect-square"></div>
          </div>
        </div>
      </div>
      <div id="home" className="flex w-full h-[90vh] pt-[5%] bg-[linear-gradient(to_bottom,rgba(121,44,26,0.7),rgba(105,34,16,0.9)),url('/images/PDM-Facade.png')] bg-cover bg-center bg-no-repeat">
        <div className="flex flex-col h-full items-center justify-center w-full pb-60">

          <div className="text-yellow-400 text-center text-[clamp(5rem,6vw,9rem)] w-fit font-medium font-serif leading-[100%] mb-7">
            Learning Made Smarter
          </div>
          <div className="text-white text-[clamp(1rem,1.8vw,5rem)] mb-10 font-medium ">
            Pambayang Dalubhasaan ng Marilao
          </div>
          <div className="flex gap-7 w-full justify-center">
            <button onClick={() => setScrollPage("guide")} className="text-white cursor-pointer w-[10vw] py-[1%] font-bold text-[clamp(1rem,1.3vw,2rem)] rounded-md border-white border-2 shadow-md shadow-black hover:scale-105 transition-all duration-300">
              User Guide
            </button>
            <button
            onClick={goChat}
            className="text-amber-950 cursor-pointer w-[10vw] py-[1%] font-bold text-[clamp(1rem,1.3vw,2rem)] rounded-md bg-amber-400 shadow-md shadow-black hover:scale-105 transition-all duration-300">
              Try AI
          </button>
          </div>
        </div>
      </div>
      <div id="guide" className=" bg-white w-full h-[100vh] flex flex-col">
        <div className="flex w-full items-center justify-center h-[35vh] mt-[-6%]">
          {buttons.map((btn, index) => (
            <button
              key={btn.id}
              onClick={() => { 
                setActiveIndex(index);
                setActiveView(index)}}
              className={`
                w-[23%] 
                h-[80%] 
                duration-300 
                transform 
                ${activeIndex === index ? "scale-105 z-1 bg-amber-500 text-white shadow-2xl rounded-sm" : "scale-100 bg-white shadow-lg"} 
                hover:scale-105
                flex flex-col items-center justify-center
              `}
            >
              <img
                src={activeIndex === index ? btn.activeImg : btn.defaultImg}
                alt={btn.title}
                className="w-40 h-40 object-contain mb-2"
                draggable={false}
              />
              <div className="flex flex-col font-sans">
                <h1 className="text-[clamp(1rem,2vw,3rem)] font-bold">{btn.title}</h1>
                <h2 className="text-[clamp(0.6rem,1vw,2rem)] ">{btn.subtitle}</h2>
              </div>
                {btn.content}
              </button>
          ))}
        </div>

        <div className="w-full h-[60vh] relative">
          <div className={`${activeView === 0 ? "flex" : "hidden"} w-full h-full justify-center items-center`}>
            <CreatingAccount />
          </div>
          <div className={`${activeView === 1 ? "flex" : "hidden"} w-full h-full justify-center items-center`}>
            <UsingApp />
          </div>
          <div className={`${activeView === 2 ? "flex" : "hidden"} w-full h-full justify-center items-center`}>
            <NavigatingApp />
          </div>
        </div>
      </div>

      <div id="programs" className=" flex flex-row items-center justify-center shadow-lg shadow-gray-400 bg-amber-500 w-full h-90 z-1">
        <div className="w-[80%] h-[110%] shadow-lg shadow-gray-700 bg-amber-900">
          <CourseDisplay />
        </div>
      </div>

      <div id="about" className="w-full h-[100vh] bg-white"></div>

      
    </div>
    </>
  );
}

export default Dashboard;
