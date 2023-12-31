import { useState } from 'react';
import { useAuthContext } from '../context/AuthContext';
import { useNavigate } from 'react-router-dom';

function useLogin() {
  const [error, setError] = useState(null);
  const [isSucc, setIsSucc] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const { dispatch } = useAuthContext();
  const navigate = useNavigate();

  const login = async (email, password) => {
    setIsSucc(false);
    setIsLoading(true);
    setError(false);

    const res = await fetch('api/login', {
      method: 'POST',
      headers: {
        'Content-type': 'application/json'
      },
      body: JSON.stringify({ email, password })
    });

    const data = await res.json();

    // console.log(data);

    if (!res.ok || data.error) {
      console.log(data, res);
      setIsLoading(false);
      setIsSucc(false);
      //Some error -  refer to userController to see what error was thrown and most imp-the err property name
      setError(data.error);
    } else if (res.ok) {
      // localStorage.setItem('user', JSON.stringify(data));
      dispatch({ type: 'LOGIN', payload: data });

      setError(false);
      setIsLoading(false);
      setIsSucc(true);
      setTimeout(() => {
        navigate('/recommended', { replace: true });
      }, 1000);
    }
  };

  return { login, error, isLoading, isSucc };
}

export default useLogin;
