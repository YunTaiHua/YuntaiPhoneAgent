Source：https://github.com/ZeroLu/awesome-nanobanana-pro

## 📖 Table of Contents

1. [写实与美学](#1-写实与美学)
2. [创意实验](#2-创意实验)
3. [教育与知识](#3-教育与知识)
4. [电子商务与虚拟工作室](#4-电子商务与虚拟工作室)
5. [工作场所与生产力](#5-工作场所与生产力)
6. [照片编辑与修复](#6-照片编辑与修复)
7. [室内设计](#7-室内设计)
8. [社交媒体与市场营销](#8-社交媒体与市场营销)
9. [日常生活与翻译](#9-日常生活与翻译)
10. [社交网络与虚拟形象](#10-社交网络与虚拟形象)

---

## 1. 写实与美学

用这些高保真提示优化你的视觉输出。这些模型旨在利用模型渲染复杂光照、纹理和特定时代的能力。

### 1.1. 超写实人群组成
*处理复杂构图，包括多位知名人物和特定光线。*
<img width="400" alt="Celebrity Crowd" src="https://github.com/user-attachments/assets/3a056a8d-904e-4b3e-b0d2-b5122758b7f5" />

**Prompt:**
```text
Create a hyper-realistic, ultra-sharp, full-color large-format image featuring a massive group of celebrities from different eras, all standing together in a single wide cinematic frame. The image must look like a perfectly photographed editorial cover with impeccable lighting, lifelike skin texture, micro-details of hair, pores, reflections, and fabric fibers.

GENERAL STYLE & MOOD: Photorealistic, 8k, shallow depth of field, soft natural fill light + strong golden rim light. High dynamic range, calibrated color grading. Skin tones perfectly accurate. Crisp fabric detail with individual threads visible. Balanced composition, slightly wide-angle lens (35mm), center-weighted. All celebrities interacting naturally, smiling, posing, or conversing. Minimal background noise, but with enough world-building to feel real.

THE ENVIRONMENT: A luxurious open-air rooftop terrace at sunset overlooking a modern city skyline. Elements include: Warm golden light wrapping around silhouettes. Polished marble.
```
*Source: [@SebJefferies](https://x.com/SebJefferies/status/1991531687147360728)*

### 1.2. 2000年代镜子自拍
*一个结构化的JSON提示，旨在生成真实的2000年代初美学，结合闪光灯摄影和怀旧元素。*
<img width="300" height="400" alt="Image" src="https://github.com/user-attachments/assets/b71755dc-ff33-4872-8161-3f5066e0ccb6" />

**Prompt:**
```json
Create a 2000s Mirror Selfie of yourself using Gemini Nano Banana.

{
  "subject": {
    "description": "A young woman taking a mirror selfie with very long voluminous dark waves and soft wispy bangs",
    "age": "young adult",
    "expression": "confident and slightly playful",
    "hair": {
      "color": "dark",
      "style": "very long, voluminous waves with soft wispy bangs"
    },
    "clothing": {
      "top": {
        "type": "fitted cropped t-shirt",
        "color": "cream white",
        "details": "features a large cute anime-style cat face graphic with big blue eyes, whiskers, and a small pink mouth"
      }
    },
    "face": {
      "preserve_original": true,
      "makeup": "natural glam makeup with soft pink dewy blush and glossy red pouty lips"
    }
  },
  "accessories": {
    "earrings": {
      "type": "gold geometric hoop earrings"
    },
    "jewelry": {
      "waistchain": "silver waistchain"
    },
    "device": {
      "type": "smartphone",
      "details": "patterned case"
    }
  },
  "photography": {
    "camera_style": "early-2000s digital camera aesthetic",
    "lighting": "harsh super-flash with bright blown-out highlights but subject still visible",
    "angle": "mirror selfie",
    "shot_type": "tight selfie composition",
    "texture": "subtle grain, retro highlights, V6 realism, crisp details, soft shadows"
  },
  "background": {
    "setting": "nostalgic early-2000s bedroom",
    "wall_color": "pastel tones",
    "elements": [
      "chunky wooden dresser",
      "CD player",
      "posters of 2000s pop icons",
      "hanging beaded door curtain",
      "cluttered vanity with lip glosses"
    ],
    "atmosphere": "authentic 2000s nostalgic vibe",
    "lighting": "retro"
  }
}
```
*Source: [@ZaraIrahh](https://x.com/ZaraIrahh/status/1991681614368436468?s=20)*

### 1.3. 维多利亚的秘密风格拍摄
*非常适合拍摄高华丽、带有复杂细节的后台时尚摄影。*
<img width="300" height="400" alt="Image" src="https://github.com/user-attachments/assets/963c0a46-cf86-4604-8782-524b94afc51d" />

**Prompt:**
```text
Create a glamorous photoshoot in the style of Victoria's Secret. A young woman attached in the uploaded reference image ( Keep the face of the person 100% accurate from the reference image ) stands almost sideways, slightly bent forward, during the final preparation for the show. Makeup artists apply lipstick to her (only her hands are visible in the frame). She is wearing a corset decorated with beaded embroidery and crystals with a short fluffy skirt, as well as large feather wings. The image has a "backstage" effect.

The background is a darkly lit room, probably under the podium. The main emphasis is on the girl's face and the details of her costume. Emphasize the expressiveness of the gaze and the luxurious look of the outfit. The photo is lit by a flash from the camera, which emphasizes the shine of the beads and crystals on the corset, as well as the girl's shiny skin. Victoria's Secret style: sensuality, luxury, glamour. Very detailed. Important: do not change the face.
```
*Source: [@NanoBanana_labs](https://x.com/NanoBanana_labs/status/1991947916479762788?s=20)*

### 1.4. 1990年代相机风格肖像
*测试模型复制特定胶片纹理、闪光灯摄影和时代氛围的能力。*
<img width="400" height="400" alt="Image" src="https://github.com/user-attachments/assets/eca5066b-1bf6-4a97-8b81-63e9e7435050" />

**Prompt:**
```text
Without changing her original face, create a portrait of a beautiful young woman with porcelain-white skin, captured with a 1990s-style camera using a direct front flash. Her messy dark brown hair is tied up, posing with a calm yet playful smile. She wears a modern oversized cream sweater. The background is a dark white wall covered with aesthetic magazine posters and stickers, evoking a cozy bedroom or personal room atmosphere under dim lighting. The 35mm lens flash creates a nostalgic glow.
```
*Source: [@kingofdairyque](https://x.com/kingofdairyque/status/1991780760030961768?s=20)*

### 1.5. 一键商务照片（硅谷风格）
*使用特定镜头和灯光说明，将随意照片转化为专业工作室头像照。*
<p align="center">
  <img width="200" src="https://github.com/user-attachments/assets/e41db56f-d928-400c-b21b-f8a0d53ba91b" alt="Original" />
  <img width="250" src="https://github.com/user-attachments/assets/793ad242-7867-4709-bdc6-55021f5eb78f" alt="Generated" />
</p>

**Prompt:**
```text
Keep the facial features of the person in the uploaded image exactly consistent . Dress them in a professional navy blue business suit with a white shirt, similar to the reference image. Background : Place the subject against a clean, solid dark gray studio photography backdrop . The background should have a subtle gradient , slightly lighter behind the subject and darker towards the edges (vignette effect). There should be no other objects. Photography Style : Shot on a Sony A7III with an 85mm f/1.4 lens , creating a flattering portrait compression. Lighting : Use a classic three-point lighting setup . The main key light should create soft, defining shadows on the face. A subtle rim light should separate the subject's shoulders and hair from the dark background. Crucial Details : Render natural skin texture with visible pores , not an airbrushed look. Add natural catchlights to the eyes . The fabric of the suit should show a subtle wool texture.Final image should be an ultra-realistic, 8k professional headshot.
```
*Source: [WeChat Article](https://mp.weixin.qq.com/s/lrYNbs4rGs3KOqewoZ6aNQ)*

### 1.6. 情感胶片摄影
*营造出电影感十足、怀旧的“柯达肖像”风格，同时保持面部一致性。*
<p align="center">
  <img width="200" src="https://github.com/user-attachments/assets/e41db56f-d928-400c-b21b-f8a0d53ba91b" alt="Original" />
  <img width="250" src="https://github.com/user-attachments/assets/243d1b11-9ef0-4d4f-b308-97d67b5d3bc3" alt="Generated" />
</p>

**Prompt:**
```text
Keep the facial features of the person in the uploaded image exactly consistent . Style : A cinematic, emotional portrait shot on Kodak Portra 400 film . Setting : An urban street coffee shop window at Golden Hour (sunset) . Warm, nostalgic lighting hitting the side of the face. Atmosphere : Apply a subtle film grain and soft focus to create a dreamy, storytelling vibe. Action : The subject is looking slightly away from the camera, holding a coffee cup, with a relaxed, candid expression. Details : High quality, depth of field, bokeh background of city lights.
```
*Source: [WeChat Article](https://mp.weixin.qq.com/s/lrYNbs4rGs3KOqewoZ6aNQ)*

### 1.7. 专业头像创作者
*从自拍制作专业头像。*
<img width="400" alt="Image" src="https://pbs.twimg.com/media/G6x00O_XIAASY0r?format=jpg&name=900x900" />

**Prompt:**
```text
"A professional, high-resolution profile photo, maintaining the exact facial structure, identity, and key features of the person in the input image. The subject is framed from the chest up, with ample headroom. The person looks directly at the camera. They are styled for a professional photo studio shoot, wearing a premium smart casual blazer in a subtle charcoal gray. The background is a solid '#562226' neutral studio color. Shot from a high angle with bright and airy soft, diffused studio lighting, gently illuminating the face and creating a subtle catchlight in the eyes, conveying a sense of clarity. Captured on an 85mm f/1.8 lens with a shallow depth of field, exquisite focus on the eyes, and beautiful, soft bokeh. Observe crisp detail on the fabric texture of the blazer, individual strands of hair, and natural, realistic skin texture. The atmosphere exudes confidence, professionalism, and approachability. Clean and bright cinematic color grading with subtle warmth and balanced tones, ensuring a polished and contemporary feel."
```
*Source: [@PavolRusnak](https://x.com/PavolRusnak/status/1994097306526994558)*

### 1.8. 超写实动漫肖像聚焦
*一幅超写实的动漫风格肖像，配有戏剧性的光影。*
<img width="400" alt="Anime Portrait Spotlight" src="https://pbs.twimg.com/media/G7Ah9SIbIAAGlyu?format=jpg&name=900x900" />

**Prompt:**
```text
Generate a hyperrealistic realistic-anime portrait of a female character standing in a completely black background.
Lighting: use a **narrow beam spotlight** focused only on the center of the face. 
The edges of the light must be sharp and dramatic. 
All areas outside the spotlight should fall quickly into deep darkness 
(high falloff shadow), almost blending into the black background. 
Not soft lighting.
Hair: long dark hair with some strands falling over the face. The lower parts of the hair should fade into the shadows.
Pose: one hand raised gently to the lips in a shy, hesitant gesture. 
Eyes looking directly at the camera with a mysterious mood.
Clothing: black long-sleeve knit sweater; 
the sweater and body should mostly disappear into the darkness with minimal detail.
Overall tone: dark, moody, dramatic, mysterious. 
High-contrast only in the lit portion of the face. 
Everything outside the spotlight should be nearly invisible.
```
*Source: Anissa ([@SimplyAnnisa](https://x.com/SimplyAnnisa)) - [Post](https://x.com/SimplyAnnisa/status/1995131975351562274?s=20)*

### 1.9. 浴室镜子自拍
*制作一张带有特定造型和构图的自然镜自拍。*
<img width="400" alt="Bathroom Mirror Selfie" src="https://pbs.twimg.com/media/G7PebGOW8AALh2P?format=jpg&name=large" />

**Prompt:**
```json
{
  "subject": {
    "description": "Young woman taking bathroom mirror selfie, innocent doe eyes but the outfit tells another story",
    "mirror_rules": "facing mirror, hips slightly angled, close to mirror filling frame",
    "age": "early 20s",
    
    "expression": {
      "eyes": "big innocent doe eyes looking up through lashes, 'who me?' energy",
      "mouth": "soft pout, lips slightly parted, maybe tiny tongue touching corner",
      "brows": "soft, slightly raised, faux innocent",
      "overall": "angel face but devil body, the contrast is the whole point"
    },
    
    "hair": {
      "color": "platinum blonde",
      "style": "messy bun or claw clip, loose strands framing face, effortless"
    },
    
    "body": {
      "waist": "tiny",
      "ass": "round, full, fabric of shorts riding up and clinging between cheeks, every curve visible through thin athletic material",
      "thighs": "thick, soft, shorts barely containing"
    },
    
    "clothing": {
      "top": {
        "type": "ULTRA mini crop tee",
        "color": "yellow",
        "graphic": "single BANANA logo/graphic",
        "fit": "barely containing chest, fabric stretched tight, ends just below, shows full stomach"
      },
      "bottom": {
        "type": "tight tennis skort or athletic booty shorts",
        "color": "white",
        "material": "thin stretchy athletic fabric",
        "fit": "vacuum tight, riding up, clinging between cheeks, fabric creases visible, leaving nothing to imagination"
      }
    },
    
    "face": {
      "features": "pretty - big eyes, small nose, full lips",
      "makeup": "minimal, natural, lip gloss, no-makeup makeup"
    }
  },

  "accessories": {
    "headwear": {
      "type": "Goorin Bros cap",
      "details": "black with animal patch, worn backwards or tilted"
    },
    "headphones": {
      "type": "over-ear white headphones",
      "position": "around neck"
    },
    "device": {
      "type": "iPhone",
      "details": "visible in mirror, held at chest level"
    }
  },

  "photography": {
    "camera_style": "casual iPhone mirror selfie, NOT professional",
    "quality": "iPhone camera - good but not studio, realistic social media quality",
    "angle": "eye-level, straight on mirror",
    "shot_type": "3/4 body, close to mirror",
    "aspect_ratio": "9:16 vertical",
    "texture": "natural, slightly grainy iPhone look, not over-processed"
  },

  "background": {
    "setting": "regular apartment bathroom",
    "style": "normal NYC apartment bathroom, not luxury",
    "elements": [
      "white subway tile walls",
      "basic bathroom mirror with good lighting above",
      "simple white sink vanity",
      "toiletries visible - skincare bottles, toothbrush holder",
      "towel hanging on hook",
      "maybe shower curtain edge visible",
      "small plant on counter"
    ],
    "atmosphere": "real bathroom, lived-in, normal home",
    "lighting": "good vanity lighting above mirror - bright, even, flattering but not studio"
  },

  "vibe": {
    "energy": "innocent face + sinful body = the whole game",
    "mood": "just got ready for tennis but making content first, 'what?' expression while wearing basically nothing",
    "contrast": "doe eyes + ass eating the shorts = lethal",
    "caption_energy": "'tennis anyone? 🍌' or 'running late oops'"
  }
}
```
*Source: gauche ([@gaucheai](https://x.com/gaucheai)) - [Post](https://x.com/gaucheai/status/1996184483343520186?s=20)*

### 1.10. 黑板动画艺术资料
*黑板动漫画作的写实记录。*
<img width="400" alt="Chalkboard Anime Art" src="https://pbs.twimg.com/media/G65Uh3ebkAEqbv5?format=jpg&name=medium" />

**Prompt:**
```json
{
  "intent": "Photorealistic documentation of a specific chalkboard art piece featuring a single anime character, capturing the ephemeral nature of the medium within a classroom context.",
  "frame": {
    "aspect_ratio": "4:3",
    "composition": "A centered medium shot focusing on the chalkboard mural. The composition includes the teacher's desk in the immediate foreground to provide scale, with the artwork of the single character dominating the background space.",
    "style_mode": "documentary_realism, texture-focused, ambient naturalism"
  },
  "subject": {
    "primary_subject": "A large-scale, intricate chalk drawing of Boa Hancock from 'One Piece' on a standard green classroom blackboard.",
    "visual_details": "The illustration depicts Boa Hancock in a commanding pose, positioned centrally on the board. She is drawn with her signature long, straight black hair with a hime cut, rendered using dense application of black chalk with white accents for sheen. Her expression is haughty and imperious, with detailed dark blue eyes. She is depicted forming a heart shape with her hands, referencing her 'Mero Mero Mellow' technique. She wears a revealing red blouse with purple geometric patterns and gold snake-shaped earrings, drawn with vibrant colored chalks.",
    "medium_texture": "The image preserves the dusty, matte quality of the chalk. Visible hatching and cross-hatching strokes create shading on her clothing and hair. Smudged areas on the green slate indicate where colors have been blended by hand.",
    "surrounding_elements": "To the right of the character, vertical Japanese text reading '海賊女帝' (Pirate Empress) is written in crisp white chalk."
  },
  "environment": {
    "location": "A standard Japanese school classroom.",
    "foreground_elements": "A wooden teacher's desk occupies the lower foreground. Scattered across the surface are a yellow box of colored chalks, loose sticks of red, white, and blue pastel chalk, and a dust-covered black felt eraser.",
    "background_elements": "The green chalkboard spans the width of the frame, bordered by a metallic chalk tray containing accumulated chalk dust. The wall above is a plain, off-white plaster, featuring a small mounted speaker box.",
    "atmosphere": "Quiet and academic, with a sense of stillness suggesting the room is currently unoccupied."
  },
  "lighting": {
    "type": "Diffuse ambient classroom lighting.",
    "quality": "Soft, nondirectional illumination provided by overhead fluorescent fixtures mixed with daylight from windows on the left. The light is even, preventing glare on the chalkboard surface while highlighting the texture of the chalk.",
    "color_temperature": "Neutral white, approximately 5000K, ensuring accurate color rendition of the red and purple chalks against the dark green board.",
    "direction": "Overhead and slightly frontal."
  },
  "camera": {
    "sensor_format": "35mm full-frame digital sensor.",
    "lens": "35mm prime lens.",
    "aperture": "f/5.6",
    "depth_of_field": "Moderate depth of field, keeping the chalkboard drawing in sharp focus while allowing the foreground desk elements to soften slightly.",
    "shutter_speed": "1/60s",
    "iso": "400",
    "camera_position": "Eye-level standing position, set back enough to frame the entire drawing and the desk."
  },
  "negative": {
    "content": "Multiple characters, Midoriya, Shigaraki, male characters, digital art overlay, vector graphics, paper texture, oil painting, messy composition, extreme low angle, fisheye lens.",
    "style": "No hyper-saturation, no soft focus filters, no heavy vignetting."
  }
}
```
*Source: Emily ([@IamEmily2050](https://x.com/IamEmily2050)) - [Post](https://x.com/IamEmily2050/status/1994624635300974734?s=20)*

### 1.11. 雪中小狗的肖像
*与小狗一起创作一幅冬季肖像。*
<img width="400" alt="Portrait with Puppy in Snow" src="https://pbs.twimg.com/media/G6qMd2abwAA-hAi?format=jpg&name=900x900" />

**Prompt:**
```json
{
  "image_description": {
    "subject": {
      "face": {
        "preserve_original": true,
        "reference_match": true,
        "description": "The girl's facial features, expression, and identity must remain exactly the same as the reference image."
      },
      "girl": {
        "age": "young",
        "hair": "long, wavy brown hair",
        "expression": "puckering her lips toward the camera",
        "clothing": "black hooded sweatshirt"
      },
      "puppy": {
        "type": "small white puppy",
        "eyes": "light blue",
        "expression": "calm, looking forward"
      }
    },
    "environment": {
      "setting": "outdoors in a winter scene",
      "elements": [
        "snow covering the ground",
        "bare trees in the background",
        "blurred silver car behind the girl"
      ],
      "sky": "clear light blue sky"
    },
    "mood": "cute, natural, winter outdoor moment",
    "camera_style": "soft depth of field, natural daylight, subtle winter tones"
  }
}
```
*Source: Zara ([@ZaraIrahh](https://x.com/ZaraIrahh)) - [Post](https://x.com/ZaraIrahh/status/1993560252319776812?s=20)*

### 1.12. Fisheye Movie Character Selfie
*与电影角色进行360度自拍*
<img width="400" alt="Fisheye Movie Selfie" src="https://pbs.twimg.com/media/G7Q6stnXIAAe7Vz?format=jpg&name=small" />

**Prompt:**
```text
A film-like fisheye wide-angle 360-degree selfie without any camera or phone visible in the subject's hands. A real and exaggerated selfie of [person from uploaded image] with [CHARACTERS]. They are making faces at the camera.

(more detailed version)
A hyper-realistic fisheye wide-angle selfie, captured with a vintage 35mm fisheye lens creating heavy barrel distortion. without any camera or phone visible in the subject's hands.
Subject & Action: A close-up, distorted group photo featuring [Person From Uploaded Image] taking selfie with [CHARACTERS]. Everyone is making wild, exaggerated faces, squinting slightly from the flash.
Lighting & Texture: Harsh, direct on-camera flash lighting that creates hard shadows behind the subjects. Authentic film grain, slight motion blur on the edges, and chromatic aberration. It looks like a candid, amateur snapshot as if captured during a chaotic behind-the-scenes moment, not a studio photo.
```
*Source: ΛRMIN | AI ([@Arminn_Ai](https://x.com/Arminn_Ai)) - [Post](https://x.com/Arminn_Ai/status/1996285140893622391?s=20)*

### 1.13. Character Consistency Selfie with Movie Character
*与电影角色自拍的同时保持你的特征*
<img width="400" alt="Character Consistency Selfie" src="https://pbs.twimg.com/media/G7HwgjGaYAAgJ67?format=jpg&name=small" />

**Prompt:**
```text
"I'm taking a selfie with [movie character] on the set of [movie name].

Keep the person exactly as shown in the reference image with 100% identical facial features, bone structure, skin tone, facial expression, pose, and appearance. 1:1 aspect ratio, 4K detail."
```
*Source: Rohan Paul ([@rohanpaul_ai](https://x.com/rohanpaul_ai)) - [Post](https://x.com/rohanpaul_ai/status/1995641282056925680?s=20)*

### 1.14. Museum Art Exhibition Selfie
*与古典油画合影的商业级照片*
<img width="400" alt="Museum Art Exhibition Selfie" src="https://pbs.twimg.com/media/G7N2KUIbMAAspf6?format=jpg&name=900x900" />
<img width="400" alt="image" src="https://github.com/user-attachments/assets/dd48cba7-661a-41c3-998d-e48047ecc6e0" />


**Prompt:**
```text
A commercial grade photograph of [uploaed reference image] posing inside a high-end museum exhibition space.
[the character Source: Based strictly on the uploaded reference image.
Behind them hangs a large, ornate framed classical oil painting.

The painting depicts the same person but rendered in a rich,
traditional oil painting style with thick, visible impasto brushstrokes, deep textures, and rich color palettes on canvas.
Gallery spotlights hit the textured paint surface.
Masterpiece, ultra-detailed, cinematic lighting, strong contrast, dramatic shadows, 8K UHD, highly detailed textures
, professional photography.
```
*Source: 烟花老师（一支烟花） ([@brad_zhang2024](https://x.com/brad_zhang2024)) - [Post](https://x.com/brad_zhang2024/status/1996072707348201827?s=20)*

### 1.15. Compact Camera Screen Display
*显示在小型数码相机屏幕上的照片*
<img width="400" alt="Camera Screen Display" src="https://pbs.twimg.com/media/G7NVohbbgAcUFBe?format=jpg&name=900x900" />

**Prompt:**
```text
Use facial feature of attached photo. A close-up shot of a young woman displayed on the screen of a compact Canon digital camera. The camera body surrounds the image with its buttons, dials, and textured surface visible, including the FUNC/SET wheel, DISP button, and the "IMAGE STABILIZER" label along the side. The photo on the screen shows the woman indoors at night, illuminated by a bright built-in flash that creates sharp highlights on her face and hair. She has long dark hair falling across part of her face in loose strands, with a soft, slightly open-lip expression. The flash accentuates her features against a dim, cluttered kitchen background with appliances, shelves, and metallic surfaces softly blurred. The mood is candid, raw, nostalgic, and reminiscent of early 2000s digital camera snapshots. Colors are slightly muted with cool undertones, strong flash contrast, and natural grain from the display. No text, no logos inside the photo preview itself.

Scale ratio: 4:5 vertical

Camera: compact digital camera simulation
Lens: equivalent to 28–35mm
Aperture: f/2.8
ISO: 400
Shutter speed: 1/60 with flash
White balance: auto flash
Lighting: harsh direct flash on subject, ambient low light in the background
Color grading: nostalgic digital-camera tones, high contrast flash, subtle display grain, authentic screen glow.
```
*Source: simply ([@kingofdairyque](https://x.com/kingofdairyque)) - [Post](https://x.com/kingofdairyque/status/1996033217795903655?s=20)*

### 1.16. Magazine Cover Portrait
*创建光泽杂志封面*
<img width="400" alt="Magazine Cover" src="https://pbs.twimg.com/media/G7QmCFcXoAAwaet?format=jpg&name=large" />

**Prompt:**
```text
A photo of a glossy magazine cover, the cover has the large bold words "Nano Banana Pro". The text is in a serif font, black on white, and fills the view. No other text.

In front of the text there is a dynamic portrait of a person in green and banana yellow colored high-end fashion.

Put the issue number and today's date in the corner along with a barcode and a price. The magazine is on a white shelf against a wall.
```
*Source: Nano Banana Pro ([@NanoBanana](https://x.com/NanoBanana)) - [Post](https://x.com/NanoBanana/status/1996262496802361675?s=20)*

### 1.17. Luxury Product Photography
*创建漂浮的奢华产品照片*
<img width="400" alt="Luxury Product Photography" src="https://raw.githubusercontent.com/ZeroLu/awesome-nanobanana-pro/refs/heads/main/assets/luxury-product-shot.jpg" />

**Prompt:**
```text
Product:
[BRAND] [PRODUCT NAME] - [bottle shape], [label description], [liquid color]

Scene:
Luxury product shot floating on dark water with [flower type] in [colors] arranged around it.
[Lighting style - e.g., "golden hour glow" /
"bright fresh light"] creates reflections and ripples across the water.

Mood & Style:
[Adjectives - e.g., "ethereal and luxurious" /
"fresh and clean"], high-end commercial photography, [camera angle], shallow depth of field with soft bokeh background
```
*Source: AmirMušić ([@AmirMushich](https://x.com/AmirMushich)) - [Post](https://x.com/AmirMushich/status/1974767431714304456)*

---

## 2. 创意实验

专注于推动构图、人群生成、极简主义和时间一致性的边界。

### 2.1. 星球大战"找找沃尔多"
*一个复杂的提示，测试模型处理密集人群和特定角色识别的能力。*
<img width="400" alt="Image" src="https://github.com/user-attachments/assets/439317c2-4be8-4b28-803f-36427ecca31e" />

**Prompt:**
```text
A where is waldo image showing all Star Wars characters on Tatooine

First one to pull this off. First take. Even Waldo is there.
```
*Source: [@creacas](https://x.com/creacas/status/1991585587548348513?s=20)*

### 2.2. 时光流逝的年龄变化
*展示单个主体的时间一致性和年龄变化效果。*
<img width="400" alt="Image" src="https://github.com/user-attachments/assets/74fced67-0715-46d3-b788-d9ed9e98873b" />

**Prompt:**
```text
"Generate the holiday photo of this person through the ages up to 80 years old"
```
*Source: [@dr_cintas](https://x.com/dr_cintas/status/1991888364099035581?s=20)*

### 2.3. 递归视觉效果
*展示模型处理无限循环逻辑（德罗斯特效应）的能力。*
<img width="400" alt="Recursive Cat" src="https://github.com/user-attachments/assets/f7ef5a84-e2bf-4d4e-a93e-38a23a21b9ef" />

**Prompt:**
```text
recursive image of an orange cat sitting in an office chair holding up an iPad. On the iPad is the same cat in the same scene holding up the same iPad. Repeated on each iPad.
```
*Source: [@venturetwins](https://x.com/venturetwins/status/1993174445515772086)*

### 2.4. 坐标可视化
*仅基于经纬度坐标生成特定位置和时间。*
<img width="400" alt="Image" src="https://github.com/user-attachments/assets/8629b88a-b872-43e2-a19e-855542702ac2" />

**Prompt:**
```text
35.6586° N, 139.7454° E at 19:00
```
*Source: [Replicate](https://replicate.com/)*

### 2.5. 概念可视化
*特定群体（如工程师）视觉化地理解地标的解释性渲染。*
<img width="400" alt="Image" src="https://github.com/user-attachments/assets/761380fe-0850-49e2-8589-797f10b7cb8d" />

**Prompt:**
```text
How engineers see the San Francisco Bridge
```
*Source: [Replicate](https://replicate.com/)*

### 2.6. 字面解读
*将文件名解释为视觉主体。*
<img width="400" alt="Rare Steak" src="https://replicate.delivery/xezq/piAS0s9DshbqMFXJvIfw9feWaEaNsejlRifhVgMSflvZJzzaF/tmp3u2ym4f_.jpeg" />

**Prompt:**
```text
rare.jpg
```
*Source: [Replicate](https://replicate.com/)*

### 2.7. 多主体合成
*将多个输入肖像组合成单一协调的团体照片，并带有特定表情。*
| Input References | Generated Output |
| :--- | :--- |
| <img width="100" src="https://replicate.delivery/pbxt/O61OKYNMCfhPTvuTf6SdRVwNlIpoKMeQPQw5WygFtvDwhWgh/guy.webp" /> <img width="100" src="https://replicate.delivery/pbxt/O61OK9ETMHHJO5m0qlCkGLhr5lcmbZ08U42C8PWLd4uszDQr/bob-ross.png" /> <br> <img width="100" src="https://replicate.delivery/pbxt/O61OKPSxpwgO83SLFGenwEcGNdEAirtw26cIfvuIxz8FeTvf/jennai.jpg" /> <img width="100" src="https://replicate.delivery/pbxt/O61OKGAI2lrcNy9I4tpUB4RPbsBUjcaxAjYjVlxRBHc2aIgK/01.webp" /> <br><img width="100" src="https://replicate.delivery/pbxt/O61S8cEIMPpMwEOkXnrroou1JkzoVFa0JJuhXHt05hBQ8AUq/replicate-prediction-50s6t1510hrma0ct2v5vj7jk2m.jpg" /> | <img width="400" alt="Image" src="https://github.com/user-attachments/assets/54e2a2eb-1ab4-4f2b-86a2-7a59856e615f" /> |

**Prompt:**
```text
an office team photo, everyone making a silly face
```
*Source: [Replicate](https://replicate.com/)*

### 2.8. 白板马克笔艺术
*在玻璃纹理上模拟特定绘画媒介（褪色马克笔）。*
<img width="400" alt="Musashi Whiteboard" src="https://github.com/user-attachments/assets/b399c4d9-151b-4e15-9a40-f092f7a892b9" />

**Prompt:**
```text
Create a photo of vagabonds musashi praying drawn on a glass whiteboard in a slightly faded green marker
```
*Source: [@nicdunz](https://x.com/nicdunz/status/1991556910106177849)*

### 2.9. 分割视图3D渲染 - iPhone 17 Pro
*创建一个左半部分为写实、右半部分为线框的3D渲染*
<img width="400" alt="Split View Render" src="https://pbs.twimg.com/media/G7LmGCQWYAAfp47?format=jpg&name=small" />

**Prompt:**
```text
Create a high-quality, realistic 3D render of exactly one instance of the object: [Orange iPhone 17 Pro].
The object must float freely in mid-air and be gently tilted and rotated in 3D space (not front-facing).
Use a soft, minimalist dark background in a clean 1080×1080 composition.
Left Half — Full Realism
The left half of the object should appear exactly as it looks in real life
— accurate materials, colors, textures, reflections, and proportions.
This half must be completely opaque with no transparency and no wireframe overlay.
No soft transition, no fading, no blending.
Right Half — Hard Cut Wireframe Interior
The right half must switch cleanly to a wireframe interior diagram.
The boundary between the two halves must be a perfectly vertical, perfectly sharp, crisp cut line, stretching straight from the top edge to the bottom edge of the object.
No diagonal edges, no curved slicing, no gradient.
The wireframe must use only two line colors:
Primary: white (≈80% of all lines)
Secondary: a color sampled from the dominant color of the realistic half (<20% of lines)
The wireframe lines must be thin, precise, aligned, and engineering-style.
Every wireframe component must perfectly match the geometry of the object.
Strict Single-Object Rule
Render only ONE object in the entire frame.  Render only one physical object.
Do NOT show a second object from any angle. Do NOT show a second object as a reflection, shadow, silhouette, outline, ghost image, or transparency. Do NOT show a second object for comparison or display purposes. Do NOT show both the front and the back separately.
Do NOT show an extra device behind, beside, underneath, or partially hidden.
Only one single object is allowed in the entire frame.
No duplicate objects, no mirrored back-and-front pairings, no reflections showing a second object.
The object must appear alone, floating.
Pose & Lighting:
Apply a natural, subtle tilt + rotation in 3D to make it look like a floating product visualization.
Use soft, neutral global illumination and no shadows under the object.
No extra props, no text, no labels unless explicitly requested.
```
*Source: Michal Malewicz ([@michalmalewicz](https://x.com/michalmalewicz)) - [Post](https://x.com/michalmalewicz/status/1995910758169752059?s=20)*

### 2.10. 带有地标的美国3D立体模型
*创建美国地标的等轴测3D立体模型*
<img width="400" alt="USA 3D Diorama" src="https://pbs.twimg.com/media/G7LGpq0XAAAxcIP?format=jpg&name=medium" />

**Prompt:**
```text
Create a high-detail 3D isometric diorama of the entire United States, where each state is represented as its own miniature platform. Inside each state, place a stylized, small-scale 3D model of that state's most iconic landmark. Use the same visual style as a cute, polished 3D city diorama: soft pastel colors, clean materials, smooth rounded forms, gentle shadows, and subtle reflections. Each landmark should look like a miniature model, charming, simplified, but clearly recognizable. Arrange the states in accurate geographical layout, with consistent lighting and perspective. Include state labels and landmark labels in a clean, modern font, floating above or near each model.
```
*Source: Data Exec ([@DataExec](https://x.com/DataExec)) - [Post](https://x.com/DataExec/status/1995876348879937648?s=20)*

### 2.11. 由著名食物制成的美国地图
*创建由著名食物制成的美国各州地图*
<img width="400" alt="US Food Map" src="https://pbs.twimg.com/media/G7I5dbiWwAAYOox?format=jpg&name=medium" />

**Prompt:**
```text
create a map of the US where every state is made out of its most famous food (the states should actually look like they are made of the food, not a picture of the food). Check carefully to make sure each state is right.
```
*Source: Ethan Mollick ([@emollick](https://x.com/emollick)) - [Post](https://x.com/emollick/status/1995720976068137048?s=20)*

### 2.12. 城市最高建筑3D卡通视图
*创建城市最高建筑的微型3D视图*
<img width="400" alt="City Buildings 3D View" src="https://pbs.twimg.com/media/G7GOJ7WW4AAEsNE?format=jpg&name=small" />

**Prompt:**
```text
Present a clear, side miniature 3D cartoon view of [YOUR CITY] tallest buildings. Use minimal textures with realistic materials and soft, lifelike lighting and shadows. Use a clean, minimalistic composition showing exactly the three tallest buildings in Sopot, arranged from LEFT to RIGHT in STRICT descending height order. The tallest must appear visibly tallest, the second must be clearly shorter than the first, and the third must be clearly shorter than the second.
All buildings must follow accurate relative proportions: if a building is taller in real life, it MUST be taller in the image by the same approximate ratio. No building may be visually stretched or compressed.
Each building should stand separately on a thin, simple ceramic base. Below each base, centered text should display:
Height in meters — semibold sans-serif, medium size
Year built — lighter-weight sans-serif, smaller size, directly beneath the height text
Provide consistent padding, spacing, leading, and kerning. Write "YOUR CITY NAME" centered above the buildings, using a medium-sized sans-serif font.
 No building top should overlap or touch the text above.Use accurate architectural proportions based on real-world references.Maintain consistent camera angle and identical scale for each building model.
No forced perspective. Use straight-on orthographic-style rendering. Do not exaggerate or stylize size differences beyond proportional accuracy.

Use a square 1080×1080 composition.Use a clean, neutral background. Ensure no extra objects are present.
```
*Source: Michal Malewicz ([@michalmalewicz](https://x.com/michalmalewicz)) - [Post](https://x.com/michalmalewicz/status/1995532450861080956?s=20)*

### 2.13. 3D等轴测家庭办公室插图
*创建家庭办公室的3D等轴测视图*
<img width="400" alt="3D Home Office" src="https://pbs.twimg.com/media/G7MEwTWWEAA1DkO?format=jpg&name=medium" />

**Prompt:**
```text
Based on you know about me, generate a 3D isometric colored illustration of me working from home, filled with various interior details. The visual style should be rounded, polished, and playful. --ar 1:1

[Additional details: a bichon frise and 3 monitors]
```
*Source: 宝玉 ([@dotey](https://x.com/dotey)) - [Post](https://x.com/dotey/status/1995944319677554985?s=20)*

### 2.14. 表情符号组合 - 戴墨镜的香蕉
*以谷歌风格设计组合表情符号*
<img width="400" alt="Emoji Combination" src="https://pbs.twimg.com/media/G7PmjRBXgAAVKXd?format=jpg&name=medium" />

**Prompt:**
```text
combine these emojis: 🍌 + 😎, on a white background as a google emoji design
```
*Source: Nano Banana Pro ([@NanoBanana](https://x.com/NanoBanana)) - [Post](https://x.com/NanoBanana/status/1996193397913317384?s=20)*

### 2.15. 撕纸艺术效果
*在图像的特定区域添加撕纸效果*
<img width="400" alt="Torn Paper Art" src="https://pbs.twimg.com/media/G7OpzpjbAAArAAS?format=jpg&name=900x900" />

**Prompt:**
```text
task: "edit-image: add widened torn-paper layered effect"

base_image:
  use_reference_image: true
  preserve_everything:
    - character identity
    - facial features and expression
    - hairstyle and anatomy
    - outfit design and colors
    - background, lighting, composition
    - overall art style

rules:
  - Only modify the torn-paper interior areas.
  - Do not change pose, anatomy, proportions, clothing details, shading, or scene elements.

effects:
  - effect: "torn-paper-reveal"
    placement: "across chest height"
    description:
      - Add a wide, natural horizontal tear across the chest area.
      - The torn interior uses the style defined in `interior_style`.

  - effect: "torn-paper-reveal"
    placement: "lower abdomen height"
    description:
      - Add a wide horizontal tear across the lower abdomen.
      - The torn interior uses the style defined in `interior_style`.

interior_style:
  mode: "line-art"

  style_settings:
    line-art:
      palette: "monochrome"
      line_quality: "clean, crisp"
      paper: "notebook paper with subtle ruled lines"

    sumi-e:
      palette: "black ink tones"
      brush_texture: "soft bleeding edges"
      paper: "plain textured paper"

    figure-render:
      material: "PVC-like"
      shading: "semi-realistic highlights"
      paper: "plain smooth surface"

    colored-pencil:
      stroke_texture: "visible pencil grain"
      palette: "soft layered hues"
      paper: "rough sketchbook paper"

    watercolor:
      palette: "soft transparent pigments"
      blending: "smooth bleeding"
      edges: "soft contours"
      paper: "watercolor paper texture"

    pencil-drawing:
      graphite_texture: "visible pencil grain"
      shading: "smooth gradients"
      line_quality: "mixed sharp and soft"
      tone: "gray-scale"
      paper: "notebook paper with faint ruled lines"
```
*Source: てんねん ([@munou_ac](https://x.com/munou_ac)) - [Post](https://x.com/munou_ac/status/1996129537806213597?s=20)*

### 2.16. 电影关键帧生成器
*根据参考图像生成电影关键帧和故事板*
<img width="400" alt="Image" src="https://pbs.twimg.com/media/G64FgZKXMAAXP_g?format=jpg&name=small" />

**Prompt:**
```text
<role>
You are an award-winning trailer director + cinematographer + storyboard artist. Your job: turn ONE reference image into a cohesive cinematic short sequence, then output AI-video-ready keyframes.
</role>

<input>
User provides: one reference image (image).
</input>

<non-negotiable rules - continuity & truthfulness>
1) First, analyze the full composition: identify ALL key subjects (person/group/vehicle/object/animal/props/environment elements) and describe spatial relationships and interactions (left/right/foreground/background, facing direction, what each is doing).
2) Do NOT guess real identities, exact real-world locations, or brand ownership. Stick to visible facts. Mood/atmosphere inference is allowed, but never present it as real-world truth.
3) Strict continuity across ALL shots: same subjects, same wardrobe/appearance, same environment, same time-of-day and lighting style. Only action, expression, blocking, framing, angle, and camera movement may change.
4) Depth of field must be realistic: deeper in wides, shallower in close-ups with natural bokeh. Keep ONE consistent cinematic color grade across the entire sequence.
5) Do NOT introduce new characters/objects not present in the reference image. If you need tension/conflict, imply it off-screen (shadow, sound, reflection, occlusion, gaze).
</non-negotiable rules - continuity & truthfulness>

<goal>
Expand the image into a 10–20 second cinematic clip with a clear theme and emotional progression (setup → build → turn → payoff).
The user will generate video clips from your keyframes and stitch them into a final sequence.
</goal>

<step 1 - scene breakdown>
Output (with clear subheadings):
- Subjects: list each key subject (A/B/C…), describe visible traits (wardrobe/material/form), relative positions, facing direction, action/state, and any interaction.
- Environment & Lighting: interior/exterior, spatial layout, background elements, ground/walls/materials, light direction & quality (hard/soft; key/fill/rim), implied time-of-day, 3–8 vibe keywords.
- Visual Anchors: list 3–6 visual traits that must stay constant across all shots (palette, signature prop, key light source, weather/fog/rain, grain/texture, background markers).
</step 1 - scene breakdown>

<step 2 - theme & story>
From the image, propose:
- Theme: one sentence.
- Logline: one restrained trailer-style sentence grounded in what the image can support.
- Emotional Arc: 4 beats (setup/build/turn/payoff), one line each.
</step 2 - theme & story>

<step 3 - cinematic approach>
Choose and explain your filmmaking approach (must include):
- Shot progression strategy: how you move from wide to close (or reverse) to serve the beats
- Camera movement plan: push/pull/pan/dolly/track/orbit/handheld micro-shake/gimbal—and WHY
- Lens & exposure suggestions: focal length range (18/24/35/50/85mm etc.), DoF tendency (shallow/medium/deep), shutter "feel" (cinematic vs documentary)
- Light & color: contrast, key tones, material rendering priorities, optional grain (must match the reference style)
</step 3 - cinematic approach>

<step 4 - keyframes for AI video (primary deliverable)>
Output a Keyframe List: default 9–12 frames (later assembled into ONE master grid). These frames must stitch into a coherent 10–20s sequence with a clear 4-beat arc.
Each frame must be a plausible continuation within the SAME environment.
</step 4 - keyframes for AI video>

<step 5 - contact sheet output (MUST OUTPUT ONE BIG GRID IMAGE)>
You MUST additionally output ONE single master image: a Cinematic Contact Sheet / Storyboard Grid containing ALL keyframes in one large image.
- Default grid: 3x3. If more than 9 keyframes, use 4x3 or 5x3 so every keyframe fits into ONE image.
Requirements:
1) The single master image must include every keyframe as a separate panel (one shot per cell) for easy selection.
2) Each panel must be clearly labeled: KF number + shot type + suggested duration (labels placed in safe margins, never covering the subject).
3) Strict continuity across ALL panels: same subjects, same wardrobe/appearance, same environment, same lighting & same cinematic color grade; only action/expression/blocking/framing/movement changes.
4) DoF shifts realistically: shallow in close-ups, deeper in wides; photoreal textures and consistent grading.
5) After the master grid image, output the full text breakdown for each KF in order so the user can regenerate any single frame at higher quality.
</step 5 - contact sheet output>

<final output format>
Output in this order:
A) Scene Breakdown
B) Theme & Story
C) Cinematic Approach
D) Keyframes (KF# list)
E) ONE Master Contact Sheet Image (All KFs in one grid)
</final output format>
```
*Source: [@underwoodxie96](https://x.com/underwoodxie96/status/1995109628825489647)*

### 2.17. 带有坐标的相册风格杂志封面
*一张精美的相册风格杂志封面，充分利用9:16的宽高比和精确的坐标。*
<img width="400" alt="Photo Book Style Magazine Cover" src="https://pbs.twimg.com/media/G70ZJFCXcAAn3F2?format=jpg&name=medium" />

**Prompt:**
```text
Create a beautiful, photo book style magazine cover that fully utilizes the 9:16 aspect ratio. Place the attached person at the precise coordinates of [latitude/longitude coordinate], seamlessly blending them into the scene as if they are sightseeing. Approach this task with the understanding that this is a critical page that will significantly influence visitor numbers. NEGATIVE: coordinate texts
```
*Source: Min Choi ([@minchoi](https://x.com/minchoi)) - [Post](https://x.com/minchoi/status/1998784591155409397)*

### 2.18. 漂浮国家岛屿立体模型
*一张超写实的数字海报，展示形状如特定国家的漂浮微型岛屿。*
<img width="400" alt="Floating Country Island" src="https://pbs.twimg.com/media/G75EwP0WkAEpIbm?format=jpg&name=medium" />

**Prompt:**
```text
Create an ultra-HD, hyper-realistic digital poster of a floating miniature island shaped like [COUNTRY], resting on white clouds in the sky. Blend iconic landmarks, natural landscapes (like forests, mountains, or beaches), and cultural elements unique to [COUNTRY]. Carve "[COUNTRY]" into the terrain using large white 3D letters. Add artistic details like birds (native to [COUNTRY]), cinematic lighting, vivid colors, aerial perspective, and sun reflections to enhance realism. Ultra-quality, 4K+ resolution. 1080x1080 format.
```
*Source: TechieSA ([@TechieBySA](https://x.com/TechieBySA)) - [Post](https://x.com/TechieBySA/status/1999110884879221052)*

### 2.19. 小说场景3D海报
*带有微型立体模型效果的小说或电影3D海报设计。*
<img width="400" alt="Novel Scene 3D Poster" src="https://pbs.twimg.com/media/G7uUpDraQAAC1ty?format=jpg&name=large" />

**Prompt:**
```text
Design a high-quality 3D poster for the movie/novel "Name to be added", first retrieving information about the movie/novel and famous scenes.

First, please use your knowledge base to retrieve information about this movie/novel and find a representative famous scene or core location. In the center of the image, construct this scene as a delicate axonometric 3D miniature model. The style should adopt DreamWorks Animation's delicate and soft rendering style. You need to reproduce the architectural details, character dynamics, and environmental atmosphere of that time, whether it's a storm or a quiet afternoon, naturally integrating into the model's lighting.

Regarding the background, do not use a simple pure white background. Please create a void environment with faint ink wash diffusion and flowing light mist around the model, with elegant colors, making the image look breathable and have depth, highlighting the preciousness of the central model.

Finally, for the bottom layout, please generate Chinese text. Center the novel title with a font that matches the original style. Below the title, automatically retrieve and typeset a classic description or quote about this scene from the original work, using an elegant serif font. The overall layout should be as精致balanced as a high-end museum exhibit label.
```
*Source: 歸藏(guizang.ai) ([@op7418](https://x.com/op7418)) - [Post](https://x.com/op7418/status/1998355915456790916)*

### 2.20. 微型游泳池立体模型
*超现实微型世界拼贴海报，以超大容器作为游泳池。*
<img width="400" alt="Miniature Swimming Pool" src="https://pbs.twimg.com/media/G7u3urdXEAA3R5K?format=jpg&name=small" />

**Prompt:**
```text
Surreal miniature-world collage poster featuring an oversized open blue Nivea-style tin repurposed as a whimsical swimming pool filled with glossy white "cream-water." 
Tiny sunbathers float in pastel swim rings, lounge on miniature deck chairs, and slide into the cream pool from a small blue slide.
The background is a soft, warm, lightly textured countertop surface subtle marble or matte stone, evenly lit, no heavy veins or visual noise. 
Keep the scene grounded with soft shadows beneath props and figures.
Surrounding the tin, keep the playful diorama elements: a small wooden deck with micro figures, pastel umbrellas, lounge chairs, and compact handcrafted accessories. Maintain the hovering pastel inflatables and plush cloud-like shapes, but ensure they feel like stylised decorative objects staged above the countertop 
Preserve the soft, high-saturation, toy-like aesthetic with plush textures, pastel gradients, and gentle lighting.
```
*Source: Salma ([@Salmaaboukarr](https://x.com/Salmaaboukarr)) - [Post](https://x.com/Salmaaboukarr/status/1998394870759567373)*

### 2.21. 圣诞装饰品3D角色
*将自己变成圣诞装饰品中可爱的3D角色。*
<img width="400" alt="Christmas Ornament 3D Character" src="https://pbs.twimg.com/media/G7vbusrWUAA8omH?format=jpg&name=large" />

**Prompt:**
```text
A transparent Christmas bauble hanging by a red ribbon. Inside, a tiny diorama of the person from the reference reimagined as a cute 3d chibi character. He works at a mini futuristic AI desk with three glowing holo-screens showing neural networks and code. Add tiny plants, a mini coffee cup, soft desk lighting, floating UI icons, and snow-glitter at the base. Warm magical Christmas glow, cinematic reflections on glass, cozy high-end diorama aesthetic.

Cinematic lighting, shallow depth of field, soft reflections on the glass, ultra-polished materials, high detail, festive Christmas atmosphere. Whimsical, premium, and heartwarming.
```
*Source: Pierrick Chevallier | IA ([@CharaspowerAI](https://x.com/CharaspowerAI)) - [Post](https://x.com/CharaspowerAI/status/1998432458941858282)*

### 2.22. 熨平皱纹
*一个超现实的抗衰老概念，用迷你熨斗熨平皱纹。*
<img width="400" alt="Ironing Out Wrinkles" src="https://pbs.twimg.com/media/G7b8YyVXQAALtxS?format=jpg&name=large" />

**Prompt:**
```json
{
  "prompt": "An award-winning, hyper-realist macro photograph in the style of high-concept editorial art. The image features an extreme close-up of an elderly woman's eye and cheekbone. A miniature, toy-like white and blue clothes iron is positioned on her skin, actively pressing down and ironing out deep wrinkles and crow's feet, leaving a streak of unnaturally smooth skin in its wake. A thin white cord trails organically across the texture of her face. The image demands microscopic clarity, capturing mascara clumps, skin pores, and vellus hairs. The lighting is an unforgiving, high-contrast hard flash typical of avant-garde fashion photography.",
  "subject_details": {
    "main_subject": "Elderly woman's face (Macro topography of aging skin)",
    "object": "Miniature white and blue iron with realistic plastic textures and a trailing cord",
    "action": "The iron is creating a visible, flattened path through the wrinkles, visually simulating a cosmetic procedure",
    "features": [
      "Piercing brown eye",
      "Clumped mascara on aging lashes",
      "Deeply etched crow's feet contrast with 'ironed' smooth areas",
      "Micro-details: vellus hair, capillaries, makeup powder texture"
    ]
  },
  "artistic_style": {
    "genre": ["Contemporary Pop-Surrealism", "Satirical Editorial", "Visual Metaphor"],
    "aesthetic": ["Maurizio Cattelan style", "Vivid Color", "Commercial Kitsch", "Tactile Realism"],
    "lighting": "Studio Ring Flash, High-Key, Hard Shadows, Glossy finish",
    "composition": "Macro Photography, Rule of Thirds focus on the iron"
  },
  "technical_specs": {
    "camera": "Hasselblad H6D-100c",
    "lens": "Macro 120mm f/4",
    "film_stock": "Kodak Ektar 100",
    "resolution": "8k, Unsplash award winner"
  },
  "mood": "Provocative, satirical, disturbingly pristine, humorous yet critical"
}
```
*Source: Ege ([@egeberkina](https://x.com/egeberkina)) - [Post](https://x.com/egeberkina/status/1997061102237049047)*

### 2.23. 完美等轴测摄影
*创建一张恰好完美等轴测的拍摄照片。*
<img width="400" alt="Isometric Photography" src="https://pbs.twimg.com/media/G7qgKDPX0AAEGS9?format=jpg&name=small" />

**Prompt:**
```text
Make a photo that is perfectly isometric. It is not a miniature, it is a captured photo that just happened to be perfectly isometric. It is a photo of [subject].
```
*Source: Nano Banana Pro ([@NanoBanana](https://x.com/NanoBanana)) - [Post](https://x.com/NanoBanana/status/1998085942201163905)*

### 2.24. 超广角手机屏幕替换
*使用超广角和手机屏幕替换编辑照片。*
<img width="400" alt="Wide Angle Phone Edit" src="https://pbs.twimg.com/media/G7gEwj8bIAAcFM2?format=jpg&name=small" />

**Prompt:**
```text
{
  "edit_type": "extreme_wide_angle_phone_edit",
  "source": {
    "_hint": "Base for editing the person, clothing, and atmosphere of the original image. No new characters allowed.",
    "mode": "EDIT",
    "preserve_elements": ["Person", "Face", "Hairstyle", "Clothing", "Environment style"],
    "change_rules": {
      "camera_angle": "Ultra-wide or fisheye lens (equivalent to 12-18mm)",
      "angle_options": [
        "Looking up from directly in front",
        "Looking down from directly in front", 
        "Extreme low angle",
        "High angle",
        "Tilted composition"
      ],
      "perspective_effect": "Nearby objects are exaggerated, distant objects become smaller",
      "body_parts_close_to_camera": "Bring 1-3 body parts extremely close to the camera",
      "body_part_options": [
        "Hands",
        "Feet/shoes",
        "Knees/thighs",
        "Face",
        "Shoulders/chest"
      ],
      "pose_variety": [
        "Extending one hand/leg toward the camera",
        "Squatting or lying on stomach halfway",
        "Sitting on the ground or an object",
        "Lying on the ground with legs pointed at camera",
        "Leaning body sharply toward the camera",
        "Twisting body for dynamic pose"
      ]
    },
    "phone_handling": {
      "allowed": true,
      "grip_options": [
        "One-handed", 
        "Two-handed",
        "Low angle",
        "High angle", 
        "Tilted",
        "Sideways",
        "Close to chest",
        "Close to waist",
        "Casual grip"
      ],
      "screen_replacement": {
        "target": "Only the smartphone screen portion displayed in the image",
        "source": "Second reference image",
        "fitting_rules": "Strictly match the screen shape, no stretching or compression",
        "interface_rules": "No icons, status bars, or app borders; only display content from original image"
      }
    },
    "environment_consistency": {
      "location": "Maintain the same location as the original image",
      "lighting": "Maintain direction and intensity",
      "extension_rules": "Maintain the same buildings, walls, road markings, colors, materials, and lighting style"
    },
    "global_restrictions": [
      "No new characters allowed",
      "No changes to age or gender expression of person", 
      "No clothing changes",
      "No changes to location type",
      "No text, logos, or watermarks added to image",
      "No illustration or anime style"
    ]
  }
}
```
*Source: 骑司Chase ([@qisi_ai](https://x.com/qisi_ai)) - [Post](https://x.com/qisi_ai/status/1997925279948534056)*

### 2.25. 商店橱窗卡通倒影
*创建一张人物站在商店橱窗旁的照片，橱窗显示其卡通版本。*
<img width="400" alt="Shop Window Cartoon" src="https://pbs.twimg.com/media/G7drMCfXkAAN3w0?format=jpg&name=large" />

**Prompt:**
```json
{
  "PROMPT": "Create a bright, high-end street-fashion photograph of the woman from the reference image, keeping her face, hair, body & outfit exactly the same. She stands outside a luxury toy-shop window, gently touching the glass. Inside the window display, place a full-height cartoon-style doll designed to resemble her—same features, hair, and outfit—transformed into a cute, big-eyed, stylized animated character. Crisp lighting, premium street-fashion look, realistic reflections, face unchanged.",
  "settings": {
    "style": "high-end street fashion",
    "lighting": "crisp and bright",
    "environment": "outside luxury toy-shop window",
    "subject": "woman from reference image",
    "focus": ["face", "hair", "body", "outfit"],
    "additional_elements": [
      {
        "type": "doll",
        "style": "cartoon-style, big-eyed, stylized",
        "location": "inside window display",
        "resemblance": "exact features, hair, outfit of woman"
      }
    ],
    "reflections": "realistic",
    "photorealism": true
  }
}
```
*Source: Mira ([@xmiiru_](https://x.com/xmiiru_)) - [Post](https://x.com/xmiiru_/status/1997182817235583293)*

### 2.26. 城市L形3D LED显示屏
*在城市环境中创建一个带有大型L形3D LED屏幕的场景。*
<img width="400" alt="Urban 3D LED Display" src="https://pbs.twimg.com/media/G7jPBxmXwAA7igN?format=jpg&name=small" />

**Prompt:**
```text
An enormous L-shaped glasses-free 3D LED screen situated prominently at a bustling urban intersection, designed in an iconic architectural style reminiscent of Shinjuku in Tokyo or Taikoo Li in Chengdu. The screen displays a captivating glasses-free 3D animation featuring [scene description]. The characters and objects possess striking depth and appear to break through the screen's boundaries, extending outward or floating vividly in mid-air. Under realistic daylight conditions, these elements cast lifelike shadows onto the screen's surface and surrounding buildings. Rich in intricate detail and vibrant colors, the animation seamlessly integrates with the urban setting and the bright sky overhead.

----
scene description: 
[An adorable giant kitten playfully paws at passing pedestrians, its fluffy paws and curious face extending realistically into the space around the screen.]
```
*Source: 宝玉 ([@dotey](https://x.com/dotey)) - [Post](https://x.com/dotey/status/1997574511705657772)*

### 2.27. 跨维度液体倾倒
*一个超现实场景，来自物理世界的液体倒入数字屏幕中。*
<img width="400" alt="Trans-Dimensional Liquid Pour" src="https://pbs.twimg.com/media/G7Uz7jZXoAAGEV0?format=jpg&name=900x900" />

**Prompt:**
```json
{
  "meta": {
    "type": "Creative Brief",
    "genre": "Hyper-realistic Surrealism",
    "composition_style": "Composite Portrait",
    "aspect_ratio": "Portrait (implied by 'portrait' description)"
  },
  "scene_architecture": {
    "viewpoint": {
      "type": "Photographic",
      "angle": "High-angle / Looking down",
      "framing": "Tight on central subject"
    },
    "dimensional_hierarchy": {
      "rule": "Scale disparity for surreal effect",
      "dominant_element": "iPhone 17 Pro Max (Super-scaled)",
      "subordinate_elements": ["Blue Book (Miniature)", "Pen (Miniature)"]
    }
  },
  "realm_physical": {
    "description": "The real-world environment surrounding the device.",
    "environment": {
      "surface": "Wooden table",
      "texture_attributes": ["rich grain", "tactile", "worn"]
    },
    "lighting_global": {
      "source": "Natural light",
      "temperature": "Warm",
      "shadow_quality": "Soft, diffused, volumetric"
    },
    "active_agent": {
      "identity": "Human Hand (Real)",
      "action": "Pouring",
      "position": "Entering frame laterally"
    },
    "held_object": {
      "item": "Bottle",
      "state": "Chilled (visible condensation)",
      "branding": {
        "logo_text": "Decamin",
        "placement": "Visible on label"
      },
      "contents": {
        "substance": "Water",
        "color": "Light Green",
        "state": "Liquid flow"
      }
    },
    "static_props": [
      {
        "item": "Book",
        "color": "Blue",
        "scale_notes": "Significantly smaller than phone"
      },
      {
        "item": "Pen",
        "type": "Ballpoint/Ink",
        "scale_notes": "Significantly smaller than phone"
      }
    ]
  },
  "realm_digital": {
    "description": "The content displayed on the screen.",
    "container_device": {
      "model": "iPhone 17 Pro Max",
      "state": "Screen ON",
      "orientation": "Flat on physical surface"
    },
    "screen_content": {
      "subject_identity": "mqn (Reference ID)",
      "subject_scale": "Close-up (filling screen)",
      "expression": "Happy / Smiling",
      "attire": "Winter clothing (matching reference)",
      "setting": "Winter landscape / snowy backdrop",
      "held_object_digital": {
        "item": "Drinking Glass",
        "branding": {
          "logo_text": "Decamin",
          "visibility": "Clear"
        },
        "initial_state": "Empty (waiting for pour)"
      }
    }
  },
  "surreal_bridge_event": {
    "description": "The interaction connecting the physical and digital realms.",
    "action_type": "Trans-dimensional Fluid Dynamics",
    "source": "realm_physical.held_object.contents (Light Green Water)",
    "interaction_point": "realm_digital.container_device.screen_surface",
    "destination": "realm_digital.screen_content.held_object_digital (The Glass)",
    "physics_violation_rules": {
      "rule_1": "Liquid does not splash off the glass screen surface.",
      "rule_2": "Screen surface acts as a permeable membrane solely for this liquid.",
      "rule_3": "Physical liquid transitions seamlessly into digital representation upon contact."
    },
    "visual_details": ["Sharp liquid simulation", "No surface tension on screen glass", "Fluid physically filling digital cup"]
  },
  "rendering_specifications": {
    "visual_fidelity": "Hyper-realistic",
    "texture_focus": ["Sharp fluid details", "Glass pixels", "Wood grain", "Skin texture (hand and subject)"],
    "mood": "Cinematic, warm, magical",
    "resolution_target": "8K / Highly detailed"
  }
}
```
*Source: Yaseen Khan Gul ([@YaseenK7212](https://x.com/YaseenK7212)) - [Post](https://x.com/YaseenK7212/status/1996559154240967144)*

### 2.28. 鱼眼抹茶女孩
*女孩品尝抹茶饮料的超广角鱼眼照片。*
<img width="400" alt="Fisheye Matcha Girl" src="https://pbs.twimg.com/media/G6_pAefWYAAilqz?format=jpg&name=large" />

**Prompt:**
```json
{
  "scene": {
    "environment": "sunny_boardwalk",
    "details": "wooden_planks, colorful_stalls, people_walking, distant_umbrellas",
    "lighting": "bright_midday_sun",
    "sky": "clear_blue"
  },
  "camera": {
    "lens": "ultra_wide_fisheye_12mm",
    "distance": "very_close_up",
    "distortion": "strong_exaggeration",
    "angle": "slightly_low_upward"
  },
  "subject": {
    "type": "young_person",
    "gender": "neutral",
    "expression": "curious_playful",
    "eyes": "large_due_to_lens_distortion",
    "pose": "leaning_forward_sipping_drink",
    "clothing": {
      "top": "bright_green_knit_sweater",
      "accessory": "chunky_blue_sunglasses"
    }
  },
  "drink": {
    "type": "iced_matcha_latte",
    "ice_cubes": "large_clear",
    "cup": "transparent_plastic",
    "straw": "green_white_spiral"
  },
  "effects": {
    "depth_of_field": "shallow_foreground_sharp_background_soft",
    "reflections": "glasses_show_boardwalk_and_people",
    "color_grade": "clean_natural"
  },
  "composition": {
    "focus": "face_extreme_closeup",
    "mood": "funny_intimate_casual",
    "background_elements": [
      "distant_people",
      "benches",
      "bright_shops"
    ]
  }
}
```
*Source: Ege ([@egeberkina](https://x.com/egeberkina)) - [Post](https://x.com/egeberkina/status/1995069549805187087)*

### 2.29. 佳能IXUS美学肖像
*创建具有佳能IXUS傻瓜相机美学的肖像。*
<img width="400" alt="Canon IXUS Aesthetic" src="https://pbs.twimg.com/media/G7U1z0CbQAE9zEq?format=jpg&name=medium" />

**Prompt:**
```json
{
  "image_parameters": {
    "style": "Canon IXUS aesthetic",
    "type": "Point-and-shoot photography",
    "quality": "Hyper-realistic",
    "tone": "Sharp, direct",
    "lighting_and_atmosphere": "Realistic, flash-style/direct lighting"
  },
  "subject": {
    "constraints": {
      "facial_identity": "Match reference image exactly 100%",
      "face_edits": "None allowed"
    },
    "hair": {
      "style": "Long, natural, lightly messy layered look",
      "movement": "Blowing gently in the wind",
      "details": "Strands slightly covering part of face"
    },
    "makeup": {
      "cheeks_and_nose": "Soft pink blush with blurred effect",
      "lips": "Subtle pink-orange tinted outline"
    },
    "expression": [
      "Cute",
      "Naive",
      "Cheerful",
      "Slightly sexy/undone charm"
    ],
    "pose": {
      "body_position": "Half-sitting, half-standing",
      "action": "Flicking hair"
    },
    "clothing": {
      "top": "Black strapless top",
      "bottom": "Low-waisted jeans with a floating waistline",
      "neck": "Thin black fabric choker/wrap"
    },
    "accessories": [
      "Small pendant necklace",
      "Gold watch"
    ]
  },
  "environment": {
    "setting": "Modern pub",
    "foreground_props": [
      "Round table",
      "Bottle of liquor",
      "Glass of liquor"
    ]
  }
}
```
*Source: Lex ([@lexx_aura](https://x.com/lexx_aura)) - [Post](https://x.com/lexx_aura/status/1996561195424260299)*

### 2.30. 超写实动漫肖像聚光灯
*带有戏剧性聚光灯照明的超写实动漫风格肖像。*
<img width="400" alt="Anime Spotlight Portrait" src="https://pbs.twimg.com/media/G7Ah9SIbIAAGlyu?format=jpg&name=900x900" />

**Prompt:**
```text
Generate a hyperrealistic realistic-anime portrait of a female character standing in a completely black background.
Lighting: use a **narrow beam spotlight** focused only on the center of the face. 
The edges of the light must be sharp and dramatic. 
All areas outside the spotlight should fall quickly into deep darkness 
(high falloff shadow), almost blending into the black background. 
Not soft lighting.
Hair: long dark hair with some strands falling over the face. The lower parts of the hair should fade into the shadows.
Pose: one hand raised gently to the lips in a shy, hesitant gesture. 
Eyes looking directly at the camera with a mysterious mood.
Clothing: black long-sleeve knit sweater; 
the sweater and body should mostly disappear into the darkness with minimal detail.
Overall tone: dark, moody, dramatic, mysterious. 
High-contrast only in the lit portion of the face. 
Everything outside the spotlight should be nearly invisible.
```
*Source: Anissa ([@SimplyAnnisa](https://x.com/SimplyAnnisa)) - [Post](https://x.com/SimplyAnnisa/status/1995131975351562274)*

---

## 3. 教育与知识

### 3.1. 概念可视化（文本到信息图）
*将文本概念转换为清晰的教育矢量插图。*
<img width="400" alt="Image" src="https://github.com/user-attachments/assets/bfaee21b-d6da-4345-9340-e786ce07dbed" />

**Prompt:**
```text
Create an educational infographic explaining [Photosynthesis] . Visual Elements : Illustrate the key components: The Sun, a green Plant, Water (H2O) entering roots, Carbon Dioxide (CO2) entering leaves, and Oxygen (O2) being released. Style : Clean, flat vector illustration suitable for a high school science textbook. Use arrows to show the flow of energy and matter. Labels : Label each element clearly in English .
```
*(Translation: 生成[光合作用]的教育信息图。视觉元素：太阳、植物、水入根、CO2入叶、O2释放。风格：适合高中课本的扁平矢量插图，用箭头显示流动。标签：用简体中文清晰标注。)*
*Source: [WeChat Article](https://mp.weixin.qq.com/s/lrYNbs4rGs3KOqewoZ6aNQ)*

### 3.2. 儿童蜡笔旅行日记插画
*为城市生成儿童风格的旅行日记插图*
<img width="400" alt="Image" src="https://pbs.twimg.com/media/G69WHFDW4AAv0TK?format=jpg&name=medium" />

**Prompt:**
```text
--- Prompt ---

Please create a vibrant, child-like crayon-style vertical (9:16) illustration titled "{City Name} Travel Journal."  
The artwork should look as if it were drawn by a curious child using colorful crayons, featuring a soft, warm light-toned background (such as pale yellow), combined with bright reds, blues, greens, and other cheerful colors to create a cozy, playful travel atmosphere.

I. Main Scene: Travel-Journal Style Route Map

In the center of the illustration, draw a "winding, zigzagging travel route" with arrows and dotted lines connecting multiple locations.  
The route should automatically generate recommended attractions based on {Number of Days}:

Example structure (auto-filled with {City Name}-related content):

- "Stop 1: {Attraction 1 + short fun description}"
- "Stop 2: {Attraction 2 + short fun description}"
- "Stop 3: {Attraction 3 + short fun description}"
- …
- "Final Stop: {Local signature food or souvenir + warm closing remark}"

Rules:
- If no number of days is provided, default to a 1-day highlight itinerary.

II. Surrounding Playful Elements (Auto-adapt to the City)

Add many cute doodles and child-like decorative elements around the route, such as:

1. Adorable travel characters
   - A child holding a local snack  
   - A little adventurer with a backpack

2. Q-style hand-drawn iconic landmarks
   - "{City Landmark 1}"
   - "{City Landmark 2}"
   - "{City Landmark 3}"

3. Funny signboards
   - "Don't get lost!"
   - "Crowds ahead!"
   - "Yummy food this way!"  
   (Auto-adjust contextually for the city)

4. Sticker-style short phrases
   - "{City Name} travel memories unlocked!"
   - "{City Name} food adventure!"
   - "Where to next?"

5. Cute icons of local foods
   - "{Local Food 1}"
   - "{Local Food 2}"
   - "{Local Food 3}"

6. Childlike exclamations
   - "I didn't know {City Name} was so fun!"
   - "I want to come again!"

III. Overall Art Style Requirements

- Crayon / children's hand-drawn travel diary style  
- Bright, warm, colorful palette  
- Cozy but full and lively composition  
- Emphasize the joy of exploring  
- All text should be in a cute handwritten font  
- Make the entire page feel like a young child's fun travel-journal entry  
```
*Source: [@dotey](https://x.com/dotey/status/1994908289813880915)*

### 3.3. 金融桑基图可视化
*创建专业的金融桑基图*
<img width="400" alt="Financial Sankey Diagram" src="https://pbs.twimg.com/media/G7P3UgNaYAAd1HN?format=jpg&name=medium" />

**Prompt:**
```text
[Subject]: A professional financial Sankey diagram visualizing the Income Statement of a major corporation, in the style of "App Economy Insights" and US corporate financial reports.[Visual Style]: High-fidelity vector infographic, clean minimalist aesthetic, flat design. The background is a clean, very light grey or off-white.[Color Strategy - CRITICAL]:
Analyze the [Insert Brand Name Here] logo. Extract its primary brand color (e.g., if Nvidia use neon green, if Meta use blue, if Tesla use red).
Use this primary color as the dominant theme for the main revenue flows and profit blocks.
Create a harmonious color palette based on this primary color: use saturated shades for the vertical nodes (bars) and semi-transparent, lighter opacity gradients for the flowing paths to ensure a cohesive and professional look. Avoid clashing colors.[Composition & Structure]:
Flow: A horizontal flow from Left (Revenue Sources) to Right (Net Profit).
Texture: The connecting paths (flows) must appear "silky smooth" with elegant Bezier curves, looking like liquid ribbons, not jagged lines.
Iconography: On the left side (Revenue sources), include specific, minimalist flat vector icons representing the business segments (e.g., a car icon for automotive, a cloud icon for services, a chip icon for hardware).
Branding: Place the official [Insert Brand Name Here] logo clearly at the top center or near the central revenue bar.[Details]: High resolution, 4k, sharp typography (sans-serif), professional data visualization layout. The chart clearly distinguishes between Revenue, Gross Profit, Operating Expenses, and Net Profit.
```
*Source: 饼干哥哥AGI（2.0） ([@bggg_ai](https://x.com/bggg_ai)) - [Post](https://x.com/bggg_ai/status/1996211865207316751?s=20)*

---

## 4. 电子商务与虚拟工作室

### 4.1. 虚拟模特试穿
*为模特穿上特定服装，同时保持面料纹理和灯光整合。*
<p align="center">
  <img width="150" src="https://github.com/user-attachments/assets/4ae658d3-4fdd-44c5-a1ab-9d44d04dd792" alt="Garment" />
  <img width="150" src="https://github.com/user-attachments/assets/8710a21d-9fc3-4d9a-bcfe-cd5fb6999bfb" alt="Model" />
  <img width="150" src="https://github.com/user-attachments/assets/81eaafb6-901b-424d-a197-dc1bc0bfc5bf" alt="Result" />
</p>

**Prompt:**
```text
Using Image 1 (the garment) and Image 2 (the model), create a hyper-realistic full-body fashion photo where the model is wearing the garment. Crucial Fit Details : The [T-shirt/Jacket] must drape naturally on the model's body, conforming to their posture and creating realistic folds and wrinkles . High-Fidelity Preservation : Preserve the original fabric texture, color, and any logos from Image 1 with extreme accuracy. Seamless Integration : Blend the garment into Image 2 by perfectly matching the ambient lighting, color temperature, and shadow direction . Photography Style : Clean e-commerce lookbook, shot on a Canon EOS R5 with a 50mm f/1.8 lens for a natural, professional look.
```
*Source: [WeChat Article](https://mp.weixin.qq.com/s/lrYNbs4rGs3KOqewoZ6aNQ)*

### 4.2. 专业产品摄影
*从杂乱的背景中分离产品，并将其置于高端商业摄影室环境中。*
<img width="400" alt="Image" src="https://github.com/user-attachments/assets/cdfd4934-d06a-48ee-bf28-58ce16c458c1" />

**Prompt:**
```text
Identify the main product in the uploaded photo (automatically removing any hands holding it or messy background details). Recreate it as a premium e-commerce product shot . Subject Isolation : Cleanly extract the product, completely removing any fingers, hands, or clutter . Background : Place the product on a pure white studio background (RGB 255, 255, 255) with a subtle, natural contact shadow at the base to ground it. Lighting : Use soft, commercial studio lighting to highlight the product's texture and material. Ensure even illumination with no harsh glare. Retouching : Automatically fix any lens distortion, improve sharpness, and color-correct to make the product look brand new and professional .
```
*Source: [WeChat Article](https://mp.weixin.qq.com/s/lrYNbs4rGs3KOqewoZ6aNQ)*

### 4.3. 3D Q版迷你品牌店
*为品牌创建微型3D店铺*
<img width="400" alt="Chibi Brand Store" src="https://pbs.twimg.com/media/G7BWvI8X0AApeZB?format=jpg&name=900x900" />

**Prompt:**
```text
3D chibi-style miniature concept store of {Brand Name}, creatively designed with an exterior inspired by the brand's most iconic product or packaging (such as a giant {brand's core product, e.g., chicken bucket/hamburger/donut/roast duck}). The store features two floors with large glass windows clearly showcasing the cozy and finely decorated interior: {brand's primary color}-themed decor, warm lighting, and busy staff dressed in outfits matching the brand. Adorable tiny figures stroll or sit along the street, surrounded by benches, street lamps, and potted plants, creating a charming urban scene. Rendered in a miniature cityscape style using Cinema 4D, with a blind-box toy aesthetic, rich in details and realism, and bathed in soft lighting that evokes a relaxing afternoon atmosphere. --ar 2:3
```
*Source: 宝玉 ([@dotey](https://x.com/dotey)) - [Post](https://x.com/dotey/status/1995190286775881780?s=20)*

### 4.4. 房间家具可视化
*可视化家具在空房间中的摆放效果*
<img width="400" alt="Image" src="https://pbs.twimg.com/media/G63UHDYWoAAD_Hm?format=jpg&name=medium" />
<img width="400" alt="image" src="https://github.com/user-attachments/assets/082f8bab-b098-4196-adf9-c6007a4b7006" />

**Prompt:**
```text
Show me how this room would look with furniture in it
```
*Source: [@NanoBanana](https://x.com/NanoBanana/status/1994483569625022487)*

---

## 5. 工作场所与生产力

### 5.1. 手绘流程图转企业图表
*将白板草图转换为清晰的"麦肯锡风格"矢量演示。*
<img width="400" alt="Image" src="https://github.com/user-attachments/assets/c59d3272-7525-4be0-94e3-8d642baaa659" />

**Prompt:**
```text
Convert this hand-drawn whiteboard sketch into a professional corporate flowchart suitable for a business presentation. Style Guide : Use a minimalist 'McKinsey-style' aesthetic : clean lines, ample whitespace, and a sophisticated blue-and-gray color palette. Structure : Automatically align all boxes and diamonds to a strict grid . Connect them with straight, orthogonal arrows (90-degree angles only, no curvy lines). Text : Transcribe the handwritten labels into a clear, bold Sans-Serif font (like Arial or Roboto). Output : High-resolution vector-style image on a pure white background.
```
*Source: [WeChat Article](https://mp.weixin.qq.com/s/lrYNbs4rGs3KOqewoZ6aNQ)*

### 5.2. UI手绘草图转高保真原型
*将线框涂鸦转换为逼真的移动应用模型。*
<img width="400" alt="Image" src="https://github.com/user-attachments/assets/67690896-22f8-4abc-8e89-d4779233a7ad" />

**Prompt:**
```text
Transform this rough wireframe sketch into a high-fidelity UI design mockups for a mobile app. Design System : Apply a modern, clean aesthetics similar to iOS 18 or Material Design 3 . Use rounded corners, soft drop shadows, and a vibrant primary color. Components : Intelligently interpret the sketch: turn scribbles into high-quality placeholder images , convert rough rectangles into proper buttons with gradients , and turn lines into realistic text blocks . Layout : Ensure perfect padding and consistent spacing between elements. Context : Place the design inside a realistic iPhone 16 frame mockups.
```
*Source: [WeChat Article](https://mp.weixin.qq.com/s/lrYNbs4rGs3KOqewoZ6aNQ)*

### 5.3. 杂志布局生成器
*非常适合以复杂排版在印刷格式中可视化文章。*
<img width="400" alt="Magazine Layout" src="https://github.com/user-attachments/assets/5982a68e-8c7d-4c7c-a07e-2a4a0a74770d" />

**Prompt:**
```text
Put this whole text, verbatim, into a photo of a glossy magazine article on a desk, with photos, beautiful typography design, pull quotes and brave formatting. The text: [...the unformatted article]
```
*Source: [@fofrAI](https://x.com/fofrAI/status/1991530971800182929)*

---

## 6. 照片编辑与修复

### 6.1. 构图拯救（智能外补）
*通过智能生成匹配的景色来扩展图像比例（例如，扩展到16:9）。*
<img width="400" alt="Image" src="https://github.com/user-attachments/assets/cc8c4e87-fe0f-4b8a-a610-a6d55ed0294c" />

**Prompt:**
```text
Zoom out and expand this image to a 16:9 aspect ratio (computer wallpaper size). Context Awareness : Seamlessly extend the scenery on both left and right sides. Match the original lighting, weather, and texture perfectly. Logical Completion : If there are cut-off objects (like a shoulder, a tree branch, or a building edge) on the borders, complete them naturally based on logical inference. Do not distort the original center image.
```
*Source: [WeChat Article](https://mp.weixin.qq.com/s/lrYNbs4rGs3KOqewoZ6aNQ)*

### 6.2. 智能人群移除
*从背景中移除不需要的人群，并用逻辑纹理填充空间。*
<img width="400" alt="Image" src="https://github.com/user-attachments/assets/bade2fb0-f7d8-4435-91d4-ad0b41819c9b" />

**Prompt:**
```text
Remove all the tourists/people in the background behind the main subject. Intelligent Fill : Replace them with realistic background elements that logically fit the scene (e.g., extend the cobblestone pavement, empty park benches, or grass textures). Consistency : Ensure no blurry artifacts or 'smudges' remain. The filled area must have the same grain, focus depth, and lighting as the rest of the photo.
```
*Source: [WeChat Article](https://mp.weixin.qq.com/s/lrYNbs4rGs3KOqewoZ6aNQ)*

### 6.3. 人脸检测闭路电视模拟
*创建带有人脸检测的高角度闭路电视监控拍摄*
<img width="400" alt="Image" src="https://pbs.twimg.com/media/G673aBCWUAAFUGn?format=jpg&name=900x900" />

**Prompt:**
```text
Create a high angle CCTV surveillance shot using the uploaded image as the source. Detect every visible person in the image and automatically draw a white rectangular bounding box around each face. For the most prominent person, add a large zoom in inset: a sharp, enhanced close-up of their face displayed in a floating rectangular frame connected with a thin white line.Keep the main image slightly noisy and security camera like (soft grain, slight distortion, muted colors), while the zoom in face box should be clearer, brighter, and more detailed. No text, no timestamps, no overlays except the boxes and connecting line. Maintain the original scene layout, angle, and environment of the uploaded image.
```
*Source: [@egeberkina](https://x.com/egeberkina/status/1994804061024010628)*

---

## 7. 室内设计

### 7.1. 硬装预览（平面图到设计）
*从简单的二维平面图生成完整的设计展示板，包括透视图和3D平面图。*
<p align="center">
  <img width="400" src="https://github.com/user-attachments/assets/5f5e4629-3ebe-45c6-8b90-bd4c009d2585" alt="Floor Plan" />
  <img width="400" src="https://github.com/user-attachments/assets/cf6d0304-60b6-4262-b4a1-08571f2c491e" alt="Design Board" />
</p>

**Prompt:**
```text
Based on the uploaded 2D floor plan, generate a professional interior design presentation board in a single image. Layout : The final image should be a collage with one large main image at the top, and several smaller images below it. Content of Each Panel :
1. Main Image (Top) : A wide-angle perspective view of the main living area , showing the connection between the living room and dining area.
2. Small Image (Bottom Left) : A view of the Master Bedroom , focusing on the bed and window.
3. Small Image (Bottom Middle) : A view of the Home Office / Study room .
4. Small Image (Bottom Right) : A 3D top-down floor plan view showing the furniture layout. Overall Style : Apply a consistent Modern Minimalist style with warm oak wood flooring and off-white walls across ALL images. Quality : Photorealistic rendering, soft natural lighting.
```
*Source: [WeChat Article](https://mp.weixin.qq.com/s/lrYNbs4rGs3KOqewoZ6aNQ)*

---

## 8. 社交媒体与市场营销

### 8.1. 病毒式封面图（YouTube/抖音/TikTok）
*创建引人注目的缩略图，带有文字叠加、夸张表情和鲜艳的图形。*
<p align="center">
  <img width="200" src="https://github.com/user-attachments/assets/f5c790f9-f0e2-4c4d-b274-bf4bcd1c4764" alt="Source" />
  <img width="250" src="https://github.com/user-attachments/assets/21b0d56c-a2a5-463a-9a0e-84100e9d08d8" alt="Thumbnail" />
</p>

**Prompt:**
```text
Design a viral video thumbnail using the person from Image 1. Face Consistency : Keep the person's facial features exactly the same as Image 1 , but change their expression to look excited and surprised . Action : Pose the person on the left side, pointing their finger towards the right side of the frame. Subject : On the right side, place a high-quality image of [a delicious avocado toast]. Graphics : Add a bold yellow arrow connecting the person's finger to the toast. Text : Overlay massive, pop-style text in the middle: '3分钟搞定!' (Done in 3 mins!). Use a thick white outline and drop shadow. Background : A blurred, bright kitchen background. High saturation and contrast.
```
*Source: [WeChat Article](https://mp.weixin.qq.com/s/lrYNbs4rGs3KOqewoZ6aNQ)*

### 8.2. 商业宣传海报
*设计专业的销售海报，集成文字和高质量产品摄影。*
<img width="400" alt="Image" src="https://github.com/user-attachments/assets/b65a064a-8519-4907-9497-90f00f9dba17" />

**Prompt:**
```text
Design a professional promotional poster for a [Coffee Shop]. Composition : A cinematic close-up of a steaming cup of cappuccino on a rustic wooden table, autumn leaves in the background (cozy atmosphere). Text Integration :
1. Main Title : 'Autumn Special' written in elegant, gold serif typography at the top.
2. Offer : 'Buy One Get One Free' clearly displayed in a modern badge or sticker style on the side.
3. Footer : 'Limited Time Only' in small, clean text at the bottom. Quality : Ensure all text is perfectly spelled, centered, and integrated into the image's depth of field.
```
*Source: [WeChat Article](https://mp.weixin.qq.com/s/lrYNbs4rGs3KOqewoZ6aNQ)*

---

## 9. 日常生活与翻译

### 9.1. 实体店/旅行翻译
*翻译菜单或标志，同时保留原始表面纹理（墙壁、纸张、油渍）。*
<p align="center">
  <img width="400" src="https://github.com/user-attachments/assets/9920f5ad-c6bb-4375-9255-a80f8568b0a9" alt="Original" />
  <img width="400" src="https://github.com/user-attachments/assets/46c82371-4f9d-431c-9a11-65f51862a792" alt="Translated" />
</p>

**Prompt:**
```text
Translate the Chinese dish names on the wall menu into English for foreign tourists. Texture Preservation : Crucial! Maintain the original aged, greasy, and textured look of the wall/paper. The new English text should look like it was written/printed on the same surface, with slight fading or wear to match. Currency : Keep the '¥' symbol and price numbers exactly as they are ; do not convert currency. Layout : align the English translations next to or replacing the Chinese characters naturally.
```
*Source: [WeChat Article](https://mp.weixin.qq.com/s/lrYNbs4rGs3KOqewoZ6aNQ)*

### 9.2. 数字内容本地化（漫画/表情包）
*通过擦除文本气泡并用匹配的字体替换内容来翻译漫画或表情包。*
<img width="400" alt="Image" src="https://github.com/user-attachments/assets/2cb58cf3-c05f-45d0-9f04-67fd7ba00267" />

**Prompt:**
```text
Translate the text in the speech bubbles/captions from [Japanese/English] to [Chinese]. Seamless Cleaning : Erase the original text and perfectly fill the background (e.g., the white speech bubble or the colored image background). Style Matching : Render the translated Chinese text using a casual, handwritten-style font (or bold impact font for memes) that matches the aesthetic of the original image. Fit : Ensure the text fits naturally within the bubbles without overcrowding.
```
*Source: [WeChat Article](https://mp.weixin.qq.com/s/lrYNbs4rGs3KOqewoZ6aNQ)*

---

## 10. 社交网络与虚拟形象

### 10.1. 3D 盲盒风格化身
*将肖像转换为可爱的C4D风格“Pop Mart”玩具角色。*
<p align="center">
  <img width="200" src="https://github.com/user-attachments/assets/c6c03353-f00a-4042-ba74-726b46c67541" alt="Original" />
  <img width="250" src="https://github.com/user-attachments/assets/da445a7e-cf15-44be-ad18-d66b8fb78ae8" alt="Blind Box" />
</p>

**Prompt:**
```text
Transform the person in the uploaded photo into a cute 3D Pop Mart style blind box character . Likeness : Keep key features recognizable: [hair color, glasses, hairstyle]. Style : C4D rendering, occlusion render, cute Q-version , soft studio lighting, pastel colors. Background : A simple, solid matte color background (e.g., soft blue). Detail : The character should have a smooth, plastic toy texture with a slight glossy finish. Facing forward, friendly expression.
```
*Source: [WeChat Article](https://mp.weixin.qq.com/s/lrYNbs4rGs3KOqewoZ6aNQ)*

### 10.2. 宠物表情包创作
*把宠物照片变成极简、手绘有趣的贴纸。*
<p align="center">
  <img width="400" src="https://github.com/user-attachments/assets/ed677fde-b407-4798-895d-e89c8534bd32" alt="Pet" />
  <img width="400" src="https://github.com/user-attachments/assets/9fc5866a-e62e-43b9-af83-8fa5f6421d33" alt="Meme" />
</p>

**Prompt:**
```text
Turn this photo of my [cat/dog] into a funny hand-drawn WeChat sticker . Style : Minimalist ugly-cute line drawing (doodle style). White background. Expression : Exaggerate the animal's expression to look extremely shocked/judgemental/lazy (based on photo). Accessories : Add cute little doodles like sweat drops, question marks, or sparkles around the head. Text : Add handwritten text at the bottom: 'So Dumb'. Ensure the text style is messy and funny.
```
*Source: [WeChat Article](https://mp.weixin.qq.com/s/lrYNbs4rGs3KOqewoZ6aNQ)*

### 10.3. Y2K风格剪贴簿海报多姿势
*创建带有多个姿势的Y2K风格剪贴簿海报*
<img width="400" alt="Y2K Scrapbook Poster" src="https://pbs.twimg.com/media/G7JduAQa8AEofUY?format=jpg&name=large" />

**Prompt:**
```text
facelock_identity": "true",
"accuracy": "100%",
scene"Colorful Y2K scrapbook poster aesthetic, vibrant stickers, multiple subjects wearing the same outfit and hairstyle with different poses and cutouts, colorful strokes and lines, frameless collage style. Includes: close-up shot with heart-shape fingers, full-body squatting pose supporting chin while holding a white polaroid camera, mid-shot touching cheek while blowing pink bubblegum, mid-shot smiling elegantly while holding a cat ,seated elegantly with one eye winking and peace sign, and mid-shot holding daisy flowers. Holographic textures, pastel gradients, glitter accents, playful doodles, magazine cut-out graphics, chaotic yet balanced layout, extremely artistic and visually engaging",
main_subject": {
"description": "A young Y2K-styled woman as the main focus in the center of the scrapbook collage.",
"style_pose": "Playful and confident Y2K pose — slight side hip pop, one hand holding a lens-flare keychain, face toward the camera with a cute-cool expression, slight pout, candid early-2000s photo vibe."
outfit": {
"top": "Cropped oversized sweater in pastel color with embroidered patches",
"bottom": "pastel skirt with a white belt",
"socks": "White ankle socks with colorful pastel stripes",
"shoes": "white sneakers",
"accessories": [
"Colorful plastic bracelets",
"Chunky colorful rings",
"Sparkling belly chain",
"hairstyle": 
"type": "Y2K half-up half-down",
"details": "Pastel flowers clips,thin front tendrils, wavy dark brown hair with bubblegum-pink tint on the lower strands, iconic early-2000s look."
additional_visuals": 
"Heart, star, and butterfly stickers",
"Retro sparkles",
"Polaroid frames",
"Neon outlines",
"Doodle borders",
"Magazine cutout texts: 'SO CUTE!', '199X!', 'GIRL VIBES'",
"Pastel lighting",
"Glossy dreamy retro glow",
"Ultra-aesthetic scrapbook layout"
photography_rendering": {
"color_grading": "Cinematic neon Y2K",
"lighting": "Soft flash lighting","skin_texture": "Smooth glossy finish",
"rendering": "High-detail hyperrealistic Y2K scrapbook tone",
"quality": "8K",
"composition": "Perfectly balanced and artistic"
negative_prompt": "no realism that breaks Y2K aesthetic, no modern 2020s clothing, no messy composition, no blurry face, no distorted hands, no extra limbs, no face warping, no low resolution, no grain, no muted colors, no watermark, no AI artifacts"
```
*Source: Shreya Yadav ([@ShreyaYadav___](https://x.com/ShreyaYadav___)) - [Post](https://x.com/ShreyaYadav___/status/1995760655018942720?s=20)*

### 10.4. 日本高中生快照照片
*创建日本高中生风格的快照*
<img width="400" alt="Japanese Snap Photo" src="https://pbs.twimg.com/media/G6z7gUVa0AMf1-G?format=jpg&name=small" />

**Prompt:**
```text
A daily snapshot taken with a low-quality disposable camera. A clumsy photo taken by a Japanese high school student. (Aspect ratio 3:2 is recommended)
```
*Source: SSSS_CRYPTOMAN ([@SSSS_CRYPTOMAN](https://x.com/SSSS_CRYPTOMAN)) - [Post](https://x.com/SSSS_CRYPTOMAN/status/1994245271220568233?s=20)*

### 10.5. AI皮肤分析与护肤程序
*分析皮肤并提供程序建议*
<img width="400" alt="AI Skin Analysis" src="https://pbs.twimg.com/media/G7QJQpOXEAAqAP1?format=jpg&name=large" />

**Prompt:**
```text
You are a professional skin analyst and skincare expert.
The user uploads a close-up photo of their face and may add short notes (age, allergies, current routine, pregnancy, etc.). Use ONLY what you see in the image plus the user text.
 1. Carefully inspect the skin: shine, pores, redness, blemishes, spots, texture, flaking, fine lines, dark circles, etc.
 2. Decide the main skin type: oily, dry, normal, combination, or sensitive.
 3. Identify visible issues: acne/breakouts, blackheads/whiteheads, post-acne marks, hyperpigmentation, redness, enlarged pores, uneven texture, dehydration, fine lines, dark circles, puffiness, etc.

RESPONSE FORMAT (very important)

Your answer must be plain text in this exact structure:
 1. First, write 3–6 short lines describing the skin and problems, for example:

 • overall skin type and how you know
 • where the main issues appear (forehead, cheeks, nose, chin, jawline, under-eyes)
 • how severe they look (mild / moderate / severe).

 2. On a new line, write the word in caps:
SKIN ROUTINE
 3. Under SKIN ROUTINE, give at least 5 numbered steps (1., 2., 3., …).
Each step must include:

 • what to do (e.g. "Cleanser", "Treatment serum", "Moisturizer", "Sunscreen", "Night treatment"),
 • product TYPE and key INGREDIENTS to look for (no brand names),
 • when to use it (AM, PM, or both) and how often,
 • 1 short practical instruction (how to apply, how much, any caution).

Focus on over-the-counter products only (no prescription or medical diagnosis).
If acne or irritation looks very severe or infected, clearly but kindly suggest visiting a dermatologist.
Keep the tone supportive, simple and clear.
```
*Source: Saman | AI ([@Samann_ai](https://x.com/Samann_ai)) - [Post](https://x.com/Samann_ai/status/1996230732470010064?s=20)*
