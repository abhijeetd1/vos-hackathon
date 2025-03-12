// Define possible options for each entity
const foodItems = ['mcchicken', 'fries', 'big mac', 'bigmac', 'mcnuggets', 'cheeseburger', 'happy meal', 'burger', 'mccrispy'];
const drinkItems = ['drink', 'coffee', 'frappe', 'soda'];
const drinkSizes = ['small', 'medium', 'large'];
const numbers = ['one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight'];

// Define new sentence starters
const sentenceStarters = [
    "I would love to have",
    "Could I get",
    "Would it be possible to get",
    "I'm thinking of ordering",
    "I'd appreciate"
];

// Function to generate a new sentence
function generateCombinedSentence() {
    const starter = sentenceStarters[Math.floor(Math.random() * sentenceStarters.length)];
    const food = foodItems[Math.floor(Math.random() * foodItems.length)];
    const drink = drinkItems[Math.floor(Math.random() * drinkItems.length)];
    const size = drinkSizes[Math.floor(Math.random() * drinkSizes.length)];
    const number = numbers[Math.floor(Math.random() * numbers.length)];

    // Generate a sentence with random components
    const sentence = `${starter} @sys.number:'${number}' @food-item:'${food}' and ${number} @drink-size:'${size}' @drink-item:'${drink}'`;
    return sentence;
}

// Generate a set of new variations
const newVariations = Array.from({ length: 10 }, generateCombinedSentence);

// Output the generated variations
newVariations.forEach(sentence => {
    console.log(sentence);
});
