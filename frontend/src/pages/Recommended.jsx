import { useQuery } from '@tanstack/react-query';
import { useEffect } from 'react'
import AxFetch from '../utils/axios';
import EventCard from '../components/EventCard';
import { useAuthContext } from '../context/AuthContext';

function Recommended() {

  const { state } = useAuthContext()
  const getRecommended = async () => {
    const res = await AxFetch.get('/api/recommended', { validateStatus: false })
    console.log(res.data)
    return res.data;
  }

  const { data, status, error, isLoading, refetch } = useQuery(["recommended"], getRecommended, {
    refetchOnMount: false,
    refetchOnWindowFocus: false,
    retry: false,
    // enabled: false
  })

  console.log(state, state.user)
  // useEffect(() => {
  //    console.log(status, data)
  // }, [status, data])

  return (
    <>
      {!isLoading && data.length > 0 ? <div className="container mx-auto p-4 pb-20">
        <h1 className="text-3xl text-center font-bold mt-8 mb-12">{state?.user ? "Recommended Events For You" : "Events"}</h1>
        <div className="grid gap-9 md:grid-cols-2 lg:grid-cols-3 items-start">
          {data?.map((event, index) => (
            <EventCard key={index} event={event} />
          ))}
        </div>
      </div> : <h1 className='text-3xl text-center font-bold mt-8 mb-12'>No Recommended Events for now</h1>}
      {isLoading && <div className="">Loading</div>}
    </>
  )
}

export default Recommended