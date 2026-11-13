"""Load the trained EfficientNet-B0 once and run predictions on images."""
import io
import sys

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

    def _load_image(self, data):
        try:
            img = Image.open(io.BytesIO(data))
            img = ImageOps.exif_transpose(img)  # phone photos carry rotation in EXIF
            return img.convert("RGB")
        except Exception as exc:  # PIL raises many different errors
            raise ImageError("File is not a readable image") from exc

    @torch.inference_mode()
    def predict(self, data, top_k=config.TOP_K):
        """Return [(dish, probability), ...] for the top_k classes, best first."""
        x = self.transform(self._load_image(data)).unsqueeze(0)
        probs = torch.softmax(self.model(x), dim=1)[0]
        values, indices = probs.topk(min(top_k, len(self.classes)))
        return [(self.classes[i], float(v)) for v, i in zip(values, indices)]
