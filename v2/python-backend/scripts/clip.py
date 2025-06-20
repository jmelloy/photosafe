import llm
import json
import os

import mlx_clip
import heapq


# Initialize the mlx_clip model with the given model name.
clip = mlx_clip.mlx_clip("/Users/jmelloy/mlx_clip/mlx-clip-vit-large-patch14")

min_heap = []


def insert_heap(heap, score, value):
    if len(heap) < 10:
        # Add to the heap if it's not full
        heapq.heappush(heap, (score, value))
    else:
        # Replace the smallest element if the current value is larger
        heapq.heappushpop(heap, (score, value))


for dir, _, files in os.walk("output"):
    for file in files:
        if file.endswith(".json"):
            with open(os.path.join(dir, file)) as F:
                data = json.load(F)

            if images := data.get("path_derivatives"):
                image = images[-1]
                score = data.get("score", {}).get("overall")

                insert_heap(min_heap, score, image)

                image_embeddings = clip.image_encoder(image)

                with open(os.path.join(dir, "clip.embeddings"), "w") as F:
                    F.write(json.dumps(image_embeddings))

print(min_heap)
