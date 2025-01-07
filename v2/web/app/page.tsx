import ImageGrid from "./components/ImageGrid";

export default async function Page() {
  const data = await fetch("http://go-backend:8080/assets");
  const images = await data.json();

  return (
    <div className="container mx-auto p-4">
      <h1 className="text-center text-3xl mb-4">Image Gallery</h1>
      <ImageGrid images={images} />
    </div>
  );
}
