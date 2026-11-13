// The 14 classes, in the same alphabetical order as src/classes.json.
export const DISHES = [
  "Aloo Gosht", "Chicken Biryani", "Chicken Karahi", "Chicken Tikka", "Daal",
  "Haleem", "Halwa Puri", "Nihari", "Pakora", "Palak Paneer",
  "Paratha Roll", "Pulao", "Samosa", "Seekh Kebab",
];

// Headline numbers shown on the landing page.
// Source: results/metrics_efficientnet.csv (accuracy row), 641 test images.
export const STATS = { dishes: DISHES.length, testAccuracy: "79.9%", testImages: 641 };
