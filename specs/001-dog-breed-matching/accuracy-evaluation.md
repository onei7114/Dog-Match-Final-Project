# Dog Match Accuracy Evaluation

- Sample size: 100
- Random seed: 42
- Model: `openai/clip-vit-base-patch32` at revision `3d74acf9a28c67741b2f4f2ea7635f0aaf6f0268`
- Sampling: deterministic sample from readable JPG/JPEG files in the local dataset.
- Exclusion: all evaluation photos are omitted from every prediction's reference candidates; other images from the same breed folder remain eligible.
- Correct top-folder labels: 38/100 (38.0%)
- Release gate (at least 80%): FAIL

## Local-only strategy comparison

The image-to-image result remains the production baseline until an alternative is explicitly adopted and its score semantics are documented.

| Strategy | Correct folder labels | Agreement |
|---|---:|---:|
| nearest_photo | 38/100 | 38.0% |
| breed_centroid | 37/100 | 37.0% |
| breed_top5_mean | 44/100 | 44.0% |
| top10_vote | 37/100 | 37.0% |

| Evaluation photo (relative path) | Selected breed folder | Correct |
|---|---|---:|
| `siberian husky dog/Image_11.jpg` | alaskan malamute dog | no |
| `bourbonnais pointing dog/Image_13.jpg` | auvergne pointer dog | no |
| `ariege pointing dog/Image_25.jpg` | saint germain pointer dog | no |
| `french tricolour hound dog/Image_18.jpg` | medium-sized anglo-french hound dog | no |
| `eurasian dog/Image_30.jpg` | icelandic sheepdog | no |
| `east siberian laika dog/Image_13.jpeg` | west siberian laika dog | no |
| `cairn terrier dog/Image_14.jpg` | norwich terrier dog | no |
| `border terrier dog/Image_34.JPG` | valencian terrier dog | no |
| `swedish vallhund dog/Image_29.jpg` | norwegian elkhound grey dog | no |
| `polish hunting dog/Image_33.jpg` | polish hunting dog | yes |
| `blue gascony basset dog/Image_11.jpg` | great gascony blue dog | no |
| `romanian bucovina shepherd dog/Image_4.jpg` | romanian bucovina shepherd dog | yes |
| `kerry blue terrier dog/Image_33.jpg` | kerry blue terrier dog | yes |
| `atlas mountain dog (aidi)/Image_31.jpg` | romanian bucovina shepherd dog | no |
| `artois hound dog/Image_34.jpg` | westphalian dachsbracke dog | no |
| `bohemian shepherd dog/Image_24.jpg` | bohemian shepherd dog | yes |
| `dutch schapendoes dog/Image_7.jpg` | large munsterlander dog | no |
| `english setter dog/Image_26.jpg` | english setter dog | yes |
| `norwegian elkhound black dog/Image_6.jpg` | norwegian hound dog | no |
| `russian-european laika dog/Image_26.jpg` | saarloos wolfhond dog | no |
| `ariegeois dog/Image_17.jpg` | ariegeois dog | yes |
| `portuguese water dog/Image_27.jpg` | catalan sheepdog | no |
| `danish-swedish farmdog/Image_16.jpg` | brazilian terrier dog | no |
| `west siberian laika dog/Image_34.jpg` | west siberian laika dog | yes |
| `small blue gascony dog/Image_16.jpg` | german short- haired pointing dog | no |
| `valencian terrier dog/Image_30.jpg` | greyhound dog | no |
| `polish hunting dog/Image_27.jpg` | neapolitan mastiff dog | no |
| `karst shepherd dog/Image_26.jpg` | bosnian and herzegovinian - croatian shepherd dog | no |
| `dutch shepherd dog/Image_35.jpg` | dutch shepherd dog | yes |
| `landseer (european continental type) dog/Image_18.jpg` | frisian water dog | no |
| `romanian bucovina shepherd dog/Image_17.jpg` | rafeiro of alentejo dog | no |
| `french white & black hound dog/Image_1.jpg` | french white & black hound dog | yes |
| `akita dog/Image_14.jpg` | eurasian dog | no |
| `chesapeake bay retriever dog/Image_15.jpg` | labrador retriever dog | no |
| `tyrolean hound dog/Image_13.jpg` | slovakian hound dog | no |
| `kerry blue terrier dog/Image_45.jpg` | kerry blue terrier dog | yes |
| `halden hound dog/Image_27.jpg` | ariege pointing dog | no |
| `french water dog/Image_34.jpg` | french water dog | yes |
| `central asia shepherd dog/Image_15.jpg` | coton de tulear dog | no |
| `drever dog/Image_19.jpg` | beagle dog | no |
| `griffon bruxellois dog/Image_34.jpg` | griffon bruxellois dog | yes |
| `border terrier dog/Image_3.JPG` | valencian terrier dog | no |
| `blue picardy spaniel dog/Image_9.jpg` | picardy spaniel dog | no |
| `irish water spaniel dog/Image_21.jpg` | irish water spaniel dog | yes |
| `bohemian wire-haired pointing griffon dog/Image_5.jpg` | bouvier des flandres dog | no |
| `hungarian hound - transylvanian scent hound dog/Image_33.jpg` | hungarian hound - transylvanian scent hound dog | yes |
| `hanoverian scent hound dog/Image_21.jpg` | fila brasileiro dog | no |
| `saarloos wolfhond dog/Image_21.jpg` | saarloos wolfhond dog | yes |
| `fox terrier (smooth) dog/Image_74.jpg` | fox terrier (smooth) dog | yes |
| `australian terrier dog/Image_16.jpg` | australian terrier dog | yes |
| `yakutian laika dog/Image_4.jpg` | yakutian laika dog | yes |
| `little lion dog/Image_22.jpg` | portuguese sheepdog | no |
| `picardy spaniel dog/Image_15.jpg` | german spaniel dog | no |
| `briard dog/Image_7.jpg` | briard dog | yes |
| `irish terrier dog/Image_31.jpg` | irish terrier dog | yes |
| `bichon frise dog/Image_13.JPG` | slovakian chuvach dog | no |
| `poodle dog/Image_9.jpg` | poodle dog | yes |
| `german shepherd dog/Image_24.jpg` | german hound dog | no |
| `serbian tricolour hound dog/Image_34.jpg` | serbian tricolour hound dog | yes |
| `schnauzer dog/Image_35.jpg` | schnauzer dog | yes |
| `hungarian wire-haired pointer dog/Image_1.jpg` | hungarian wire-haired pointer dog | yes |
| `pyrenean mastiff dog/Image_24.jpg` | golden retriever dog | no |
| `dachshund dog/Image_12.jpg` | italian rough-haired segugio dog | no |
| `welsh corgi (cardigan) dog/Image_18.jpg` | parson russell terrier dog | no |
| `bedlington terrier dog/Image_3.jpg` | bedlington terrier dog | yes |
| `austrian  pinscher dog/Image_20.JPG` | atlas mountain dog (aidi) | no |
| `spanish mastiff dog/Image_10.jpg` | spanish mastiff dog | yes |
| `english foxhound dog/Image_19.jpg` | harrier dog | no |
| `german hunting terrier dog/Image_27.jpg` | segugio maremmano dog | no |
| `bichon frise dog/Image_28.jpg` | bichon frise dog | yes |
| `english setter dog/Image_29.jpg` | american cocker spaniel dog | no |
| `border terrier dog/Image_10.jpg` | border terrier dog | yes |
| `irish water spaniel dog/Image_24.JPG` | puli dog | no |
| `french water dog/Image_6.jpg` | poodle dog | no |
| `large munsterlander dog/Image_24.jpg` | stabijhoun dog | no |
| `shih tzu dog/Image_18.jpg` | havanese dog | no |
| `hygen hound dog/Image_29.jpg` | great anglo-french white and black hound dog | no |
| `chihuahua dog/Image_3.jpg` | chihuahua dog | yes |
| `irish glen of imaal terrier dog/Image_27.jpg` | affenpinscher dog | no |
| `hovawart dog/Image_8.jpg` | bernese mountain dog | no |
| `dogo argentino/Image_23.jpg` | dogo argentino | yes |
| `staffordshire bull terrier dog/Image_20.jpg` | staffordshire bull terrier dog | yes |
| `fox terrier (wire) dog/Image_21.jpg` | fox terrier (wire) dog | yes |
| `valencian terrier dog/Image_6.jpg` | fox terrier (smooth) dog | no |
| `thai bangkaew dog/Image_1.jpg` | thai bangkaew dog | yes |
| `slovakian hound dog/Image_19.jpg` | norwegian lundehund dog | no |
| `belgian shepherd dog/Image_28.jpg` | schipperke dog | no |
| `saint miguel cattle dog/Image_9.jpg` | segugio maremmano dog | no |
| `shiba dog/Image_7.jpg` | korea jindo dog | no |
| `cirneco dell'etna dog/Image_34.jpg` | cirneco dell'etna dog | yes |
| `picardy sheepdog/Image_16.jpg` | portuguese warren hound-portuguese podengo dog | no |
| `yakutian laika dog/Image_28.jpg` | kishu dog | no |
| `eurasian dog/Image_29.jpg` | estrela mountain dog | no |
| `chinese crested dog/Image_1.jpg` | chinese crested dog | yes |
| `long-haired pyrenean sheepdog/Image_34.jpg` | long-haired pyrenean sheepdog | yes |
| `irish water spaniel dog/Image_13.jpg` | english cocker spaniel dog | no |
| `french bulldog/Image_33.jpg` | french bulldog | yes |
| `siberian husky dog/Image_20.jpg` | east siberian laika dog | no |
| `tibetan mastiff dog/Image_15.jpg` | tibetan mastiff dog | yes |
| `portuguese sheepdog/Image_23.jpg` | italian rough-haired segugio dog | no |
