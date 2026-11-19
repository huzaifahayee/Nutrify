"""Load the trained EfficientNet-B0 once and run predictions on images."""
import io
import sys

import numpy as np
import torch
from PIL import Image, ImageOps

from . import config

# Make `import src...` work when uvicorn is started from any folder.
if str(config.REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(config.REPO_ROOT))

from src.dataset import eval_transforms  # noqa: E402  same preprocessing as training
from src.efficientnet_model import build_efficientnet  # noqa: E402


class ImageError(ValueError):
    """The uploaded bytes are not a readable image."""


class ModelService:
    def __init__(self, checkpoint_path=config.CHECKPOINT_PATH):
        ckpt = torch.load(checkpoint_path, map_location="cpu", weights_only=False)
        self.classes = list(ckpt["classes"])
        self.model = build_efficientnet(num_classes=len(self.classes), pretrained=False)
        self.model.load_state_dict(ckpt["state_dict"])
        self.model.eval()
        self.transform = eval_transforms()
        # Dish centroids from results/ood_reference.npz (built by src/ood_analysis.py).
        self.centroids = None
        if config.OOD_REFERENCE_PATH.exists():
            c = np.load(config.OOD_REFERENCE_PATH)["centroids"]
            self.centroids = torch.from_numpy(c / np.linalg.norm(c, axis=1, keepdims=True)).float()

    def _load_image(self, data):
        try:
            img = Image.open(io.BytesIO(data))
            img = ImageOps.exif_transpose(img)  # phone photos carry rotation in EXIF
            return img.convert("RGB")
        except Exception as exc:  # PIL raises many different errors
            raise ImageError("File is not a readable image") from exc

    @torch.inference_mode()
    def predict(self, data, top_k=config.TOP_K):
        """Return the top_k [(dish, probability)] and the similarity to the nearest dish.

        similarity is None when results/ood_reference.npz does not exist.
        """
        x = self.transform(self._load_image(data)).unsqueeze(0)
        feats = self.model.avgpool(self.model.features(x)).flatten(1)
        probs = torch.softmax(self.model.classifier(feats), dim=1)[0]
        values, indices = probs.topk(min(top_k, len(self.classes)))
        top = [(self.classes[i], float(v)) for v, i in zip(values, indices)]
        similarity = None
        if self.centroids is not None:
            unit = feats / feats.norm(dim=1, keepdim=True)
            similarity = float((unit @ self.centroids.T).max())
        return top, similarity
