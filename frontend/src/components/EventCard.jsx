import { AiFillCalendar, AiFillInfoCircle, AiOutlineEnvironment } from 'react-icons/ai';
import { FiInfo } from 'react-icons/fi';
import { BiLinkExternal } from 'react-icons/bi';
import { IoCopy } from 'react-icons/io5';
import { useAuthContext } from '../context/AuthContext';
import { Link, useNavigate } from 'react-router-dom';
import { useState, useEffect } from 'react';
import useRegisterEvent from '../hooks/useRegisterEvent';
import { toast } from 'react-toastify';
import { GoCopy } from "react-icons/go";


const EventCard = ({ event }) => {
  const { name, startDate, endDate, language, email, phone, topics, venue, location, fields, description, minAge, maxAge, industry, status, genders } = event;
  const [registered, setRegistered] = useState("Loading...")
  const [showInfo, setShowInfo] = useState(false);
  const [dist, setDist] = useState(0);
  // const [copied, setCopied]= useState(false)
  const { register, error, isLoading, isSucc } = useRegisterEvent()


  const { state } = useAuthContext()
  // console.log(state?.user, fields)


  const navigate = useNavigate()

  //   const onRegisterForm=()=>{
  //         setRegistered(true)
  //   }

  useEffect(() => {

    const func = async () => {
      const res = await fetch(`/api/check-register/${event._id}`, {
        method: 'GET',
        credentials: "same-origin", //for cookies
      })
      const data = await res.json()
      setRegistered(data?.registered)
    };

    func()

  }, [event?._id])


  const handleRegistration = (e) => {
    e.preventDefault();
    if (!(state?.user)) {
      return navigate('/reg-form', {
        state: {
          fields, eid: event._id
        }
      })
    }
    if (!registered) register(state?.user, true, event._id); else register(state?.user, false, event._id)
    if (!registered) toast.success("Registered successfully!"); else toast.success("Unregistered yourself succesfully!")
    setRegistered(prev => !prev)
  }

  const isEventUnderway = new Date(startDate) <= new Date();
  const label = isEventUnderway ? 'Event underway' : 'Event yet to start';

  useEffect(() => {

    const func = async () => {
      const res = await fetch(`/api/distance`, {
        method: 'POST',
        credentials: "same-origin", //for cookies
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ location: event.coordinates })
      })
      const data = await res.json()
      setDist(data['distance'])
      console.log('HHHHHEEEEELLLLLOOO')
    };

    func()

  },)

  return (
    <div className="bg-white shadow-lg rounded-lg overflow-hidden">
      {error && (
        <div className="p-4 mb-7 w-full text-center text-sm text-red-800 rounded-lg bg-red-200  dark:text-red-700 " role="alert"> {error}
        </div>
      )}
      {/* {isSucc && (
        <div className="p-4 mb-7 w-full text-center text-sm text-green-800 rounded-lg bg-green-200  dark:text-green-700 " role="alert"> Succesfully registered</div>
      )} */}
      <div className="bg-gray-100 py-2 px-3 flex justify-between">
        <h2 className="text-sm font-bold mb-2 flex items-center">
          <span className="text-gray-600">{dist} km away</span>
          <div className="relative ml-2">
            <FiInfo
              className="text-gray-500 cursor-pointer"
              onMouseEnter={() => setShowInfo(true)}
              onMouseLeave={() => setShowInfo(false)}
            />
            {showInfo && (
              <span className="absolute bg-blue-100 text-gray-600 px-4 py-3 w-64 border border-black rounded mt-2 ml-2 text-sm">
                The organizer is collecting the following data: {fields.join(', ')}
              </span>
            )}

          </div>
        </h2>
        <div className='flex'>
          <Link state={event} to='/event-description' className='text-sm font-bold mb-2 flex items-center hover:text-green-300'><BiLinkExternal /></Link>
          <button className='mx-2 mb-2' onClick={() => {
            navigator.clipboard.writeText(`http://localhost:3000/event/${event?._id}`)
            toast.success("Event URL copied to clipboard!")
          }}><GoCopy /></button>
        </div>

      </div>
      <div className="bg-zinc-200 py-3 px-4">
        <div className="flex justify-between items-center mb-2">
          <h2 className="text-lg font-bold">{name}</h2>
          <div className={`text-sm px-3 py-2 rounded-lg text-white  ${isEventUnderway ? 'bg-blue-500' : 'bg-green-500'}`}>
            {label}
          </div>
        </div>
        <div className="flex flex-wrap mt-1">
          {topics.map((topic, index) => (
            <span
              key={index}
              className="bg-white text-gray-700 rounded-full px-2 py-1 text-xs mr-1 mt-1"
            >
              {topic}
            </span>
          ))}
        </div>
      </div>

      <div className="p-4">
        <div className="flex items-center mb-2">
          <AiFillCalendar className="text-gray-400 mr-1" />
          <span className="text-gray-600">{startDate}</span>
          <span className="text-gray-400 mx-1">-</span>
          <span className="text-gray-600">{endDate}</span>
        </div>
        <div className="flex items-center mb-2">
          <span className="text-gray-600">{venue}</span>
          <span className="text-gray-400 mx-1">|</span>
          <span className="text-gray-600">{location}</span>
        </div>
      </div>

      {(registered !== "Loading...") && state?.user && <button className={`text-white ${registered && (state?.user) ? 'bg-green-600' : 'bg-blue-600'} px-3 text-center py-2 w-full mx-0 font-sm focus:outline-none ${registered ? 'hover:bg-green-800' : 'hover:bg-blue-800'}`} onClick={handleRegistration}>
        {registered && (state?.user) ? "Registered!" : "Register"}
      </button>}
      {!(state?.user) && <div className='flex w-full'><button className={`text-white bg-green-700 px-3 text-center py-2 mx-0 font-sm focus:outline-none hover:bg-green-800 w-[50%]`} onClick={() => navigate('/signup')}>
        1Click Registration
      </button><button className={`text-white bg-blue-700 px-3 text-center py-2  mx-0 font-sm focus:outline-none w-[50%] hover:bg-blue-800`} onClick={handleRegistration}>
          Register
        </button> </div>}
    </div>
  );
};

export default EventCard;
