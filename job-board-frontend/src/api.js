import axios from 'axios';


const API_URL = process.env.REACT_APP_BACKEND_URL;



export const getJobs = async ({ limit, skip }) => {
    try {
      const response = await axios.get(`${API_URL}/jobs?limit=${limit}&skip=${skip}`);
      console.log('Jobs fetched:', response.data); // Add logging for the response
      return response.data;
    } catch (error) {
      console.error('Error fetching jobs:', error.response || error.message); // Log the error for better clarity
      throw error;
    }
  };
  