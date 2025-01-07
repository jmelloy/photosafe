"use client";

import Image from "next/image";
import { useState } from "react";

interface ImageData {
  id: number;
  thumbnail: string;
  fullSize: string;
  alt: string;
}

interface ImageGridProps {
  images: ImageData[];
}

export default function ImageGrid({ images }: ImageGridProps) {
  const [selectedImage, setSelectedImage] = useState<ImageData | null>(null);

  const handleClick = (image: ImageData) => {
    setSelectedImage(image);
  };

  return (
    <div>
      <div className="grid grid-cols-3 gap-4">
        {images.map((image) => (
          <div key={image.id} className="relative cursor-pointer">
            <Image
              src={image.thumbnail}
              alt={image.alt}
              width={200}
              height={200}
              className="object-cover"
              onClick={() => handleClick(image)}
            />
          </div>
        ))}
      </div>

      {selectedImage && (
        <div className="fixed inset-0 bg-black bg-opacity-75 flex justify-center items-center z-50">
          <div className="relative max-w-full max-h-full">
            <button
              className="absolute top-2 right-2 text-white text-2xl"
              onClick={() => setSelectedImage(null)}
            >
              &times;
            </button>
            <Image
              src={selectedImage.fullSize}
              alt={selectedImage.alt}
              width={1000}
              height={1000}
              className="object-contain"
            />
          </div>
        </div>
      )}
    </div>
  );
}
