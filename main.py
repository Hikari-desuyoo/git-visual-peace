from datetime import datetime
from PIL import Image, ImageChops, UnidentifiedImageError
from psd_tools import PSDImage
from psd_tools.api.layers import PixelLayer
from psd_tools.constants import Resource
import atexit
import io
import os
import shutil
import subprocess
import sys

# checking if git is ok and fetching stuff
if shutil.which("git") is None:
    print("command not found: git")
    sys.exit(1)

if not os.path.isdir(".git"):
    print("repository not found")
    sys.exit(1)

ours_branch = subprocess.run(
    ["git", "branch", "--show-current"], capture_output=True, text=True
).stdout.strip()

try:
    branch_and_path = sys.argv[1]
    theirs_branch, img_path = branch_and_path.split(":")
    if not img_path:
        raise ValueError
except (ValueError, IndexError):
    print("Usage: git-vp branch:filepath")
    sys.exit(1)


# setup interruption handler
def exit_handler():
    shutil.rmtree(tmp_path)


atexit.register(exit_handler)

# setup temp dirs
human_readable_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
tmp_path = rf"C:\Temp\gitvp\{human_readable_time}"
os.makedirs(tmp_path, exist_ok=True)

# setup PSD
try:
    git_show_sp = subprocess.run(
        ["git", "show", branch_and_path.replace("\\", "/")],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=True,
    )
    theirs = Image.open(io.BytesIO(git_show_sp.stdout)).convert("RGBA")
except subprocess.CalledProcessError as e:
    print(e.stderr.decode().strip())
    sys.exit(1)
except UnidentifiedImageError:
    print(f"{img_path} is not a valid image file path")
    sys.exit(1)

ours = Image.open(img_path).convert("RGBA")

w1, h1 = ours.size
w2, h2 = theirs.size
w = max(w1, w2)
h = max(h1, h2)

psd = PSDImage.new(mode="RGBA", size=(w, h))

# create normal layers
layer_ours = PixelLayer.frompil(ours, psd)
layer_ours.name = "(ours) " + ours_branch
layer_theirs = PixelLayer.frompil(theirs, psd)
layer_theirs.name = "(theirs) " + theirs_branch


# diff layer
def get_diff_image(image1, image2):
    # Compute the difference between the two images
    diff = ImageChops.difference(image1, image2)
    green_img = Image.new("RGBA", diff.size, (0, 255, 0, 255))
    red_img = Image.new("RGBA", diff.size, (255, 0, 0, 255))

    # Create a mask from the difference image
    mask = diff.convert("L").point(lambda p: 1 if p else 0, "1")

    # Composite the red diff over the green background using the mask
    result_image = Image.composite(red_img, green_img, mask)

    return result_image


diff_pil_image = get_diff_image(theirs, ours)

layer_diff = PixelLayer.frompil(diff_pil_image, psd)
layer_diff.opacity = 50
layer_diff.name = "diff"

# append layers
psd.append(layer_ours)
psd.append(layer_theirs)
psd.append(layer_diff)

# Save the PSD file
psd_path = tmp_path + "\solver.psd"
psd.save(psd_path)
print("Opening editor...")

subprocess.Popen(["start", "/wait", psd_path], shell=True)
if input("Are you done? [Y/n]").lower() == "n":
    sys.exit(0)


print(f"Saving to {img_path}...")
psd = PSDImage.open(psd_path)
icc_profile = psd.image_resources.get_data(Resource.ICC_PROFILE)
image = psd.composite(apply_icc=False)
image.save(img_path, icc_profile=icc_profile)

# git add to set conflict as resolved

subprocess.run(["git", "add", img_path])
