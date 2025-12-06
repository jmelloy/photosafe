import axios from "axios";

const API_BASE_URL = "/api";

export const getPhotos = async () => {
  const response = await axios.get(`${API_BASE_URL}/photos`);
  return response.data;
};

export const getPhoto = async (id) => {
  const response = await axios.get(`${API_BASE_URL}/photos/${id}`);
  return response.data;
};

export const uploadPhoto = async (file) => {
  const formData = new FormData();
  formData.append("file", file);

  const response = await axios.post(`${API_BASE_URL}/photos/upload`, formData, {
    headers: {
      "Content-Type": "multipart/form-data",
    },
  });
  return response.data;
};

export const deletePhoto = async (id) => {
  const response = await axios.delete(`${API_BASE_URL}/photos/${id}`);
  return response.data;
};
