import type { Media } from "./MediaCard";

export const SAMPLE_MEDIA: Media[] = [
  {
    id: "m1",
    name: "koala_eucalyptus_001.jpg",
    type: "image",
    thumbnail: "https://images.unsplash.com/photo-1680924667747-128ea49c4638?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&w=600&q=80",
    tags: [{ name: "koala", count: 3 }, { name: "tree", count: 1 }],
  },
  {
    id: "m2",
    name: "kangaroo_mob_field.jpg",
    type: "image",
    thumbnail: "https://images.unsplash.com/photo-1526515920271-2d8fc77ab015?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&w=600&q=80",
    tags: [{ name: "kangaroo", count: 5 }, { name: "grass", count: 2 }],
  },
  {
    id: "m3",
    name: "joey_in_pouch.jpg",
    type: "image",
    thumbnail: "https://images.unsplash.com/photo-1551270988-87c5ea57cdfe?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&w=600&q=80",
    tags: [{ name: "kangaroo", count: 2 }, { name: "joey", count: 1 }],
  },
  {
    id: "m4",
    name: "wombat_burrow_dusk.mp4",
    type: "video",
    thumbnail: "https://images.unsplash.com/photo-1513333420772-7b64ad15ca96?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&w=600&q=80",
    tags: [{ name: "wombat", count: 2 }],
  },
  {
    id: "m5",
    name: "kangaroo_close_up.jpg",
    type: "image",
    thumbnail: "https://images.unsplash.com/photo-1626803111824-0ee594987d4b?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&w=600&q=80",
    tags: [{ name: "kangaroo", count: 1 }],
  },
  {
    id: "m6",
    name: "kangaroo_with_joey.jpg",
    type: "image",
    thumbnail: "https://images.unsplash.com/photo-1575699914911-0027c7b95fb6?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&w=600&q=80",
    tags: [{ name: "kangaroo", count: 2 }, { name: "joey", count: 1 }],
  },
  {
    id: "m7",
    name: "kangaroo_tree.jpg",
    type: "image",
    thumbnail: "https://images.unsplash.com/photo-1709460274641-a29b02087454?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&w=600&q=80",
    tags: [{ name: "kangaroo", count: 1 }, { name: "tree", count: 1 }],
  },
  {
    id: "m8",
    name: "outback_kangaroos.mp4",
    type: "video",
    thumbnail: "https://images.unsplash.com/photo-1588475935720-845e2aacb8c6?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&w=600&q=80",
    tags: [{ name: "kangaroo", count: 4 }, { name: "outback", count: 1 }],
  },
];
