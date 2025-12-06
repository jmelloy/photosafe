import api from "./client";

export const getPhotos = async () => {
  const response = await api.get("/photos/");
  return response.data;
};

export const getPhoto = async (id) => {
  const response = await api.get(`/photos/${id}`);
  return response.data;
};

export const uploadPhoto = async (file) => {
  const formData = new FormData();
  formData.append("file", file);

  const response = await api.post("/photos/upload", formData, {
    headers: {
      "Content-Type": "multipart/form-data",
    },
  });
  return response.data;
};

export const deletePhoto = async (id) => {
  const response = await api.delete(`/photos/${id}`);
  return response.data;
};
