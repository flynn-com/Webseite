// Initial Project Data
const initialProjects = [
    {
        id: 1,
        number: "01",
        title: "Cosmic Set",
        bigNumber: "01",
        headerDetails: "CLASSIC HOODIE<br>BY FLYNN STUDIO<br>100% COTTON",
        shortDescription: "A timeless piece designed for the modern explorer. Max 250 chars.",
        description: "A timeless piece designed for the modern explorer. Crafted from premium 100% cotton, this hoodie combines comfort with an avant-garde aesthetic.",
        previewText: "PREVIEW",
        mainImageText: "PRODUCT IMG",
        gallery: [] // Array of base64 strings
    },
    {
        id: 2,
        number: "02",
        title: "Next Horizon",
        bigNumber: "02",
        headerDetails: "DIGITAL ART<br>COLLECTION",
        shortDescription: "Exploring the boundaries between digital and physical reality.",
        description: "Exploring the boundaries between digital and physical reality. This collection features generative art pieces inspired by cosmic events.",
        previewText: "",
        mainImageText: "ARTWORK IMG",
        gallery: []
    }
];

// Export initial data for seeding
// The actual storage logic is now in db.js
window.initialProjects = initialProjects;
