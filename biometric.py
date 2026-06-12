from deepface import DeepFace

def compare_faces(img1_path, img2_path):

    try:
        result = DeepFace.verify(
            img1_path=img1_path,
            img2_path=img2_path,
            enforce_detection=True
        )

        return {
            "match": result["verified"],
            "confidence": round((1 - result["distance"]) * 100, 2)
        }

    except Exception as e:
        print("Face error:", e)
        return {
            "match": False,
            "confidence": 0.0
        }