// IndexedDB Wrapper for .FLYNN projects
const DB_NAME = 'FlynnDB';
const DB_VERSION = 1;
const STORE_NAME = 'projects';

console.log("Loading db.js...");

const dbPromise = new Promise((resolve, reject) => {
    const request = indexedDB.open(DB_NAME, DB_VERSION);

    request.onupgradeneeded = (e) => {
        console.log("Upgrading DB...");
        const db = e.target.result;
        if (!db.objectStoreNames.contains(STORE_NAME)) {
            db.createObjectStore(STORE_NAME, { keyPath: 'id' });
        }
    };

    request.onsuccess = (e) => {
        console.log("DB Opened successfully");
        resolve(e.target.result);
    };
    request.onerror = (e) => {
        console.error("DB Error", e);
        reject('DB Error: ' + e.target.error);
    };
});

const ProjectDB = {
    async getAll() {
        const db = await dbPromise;
        return new Promise((resolve, reject) => {
            const tx = db.transaction(STORE_NAME, 'readonly');
            const store = tx.objectStore(STORE_NAME);
            const req = store.getAll();
            req.onsuccess = () => resolve(req.result || []);
            req.onerror = () => reject(req.error);
        });
    },

    async save(project) {
        const db = await dbPromise;
        return new Promise((resolve, reject) => {
            const tx = db.transaction(STORE_NAME, 'readwrite');
            const store = tx.objectStore(STORE_NAME);
            const req = store.put(project);
            req.onsuccess = () => resolve(req.result);
            req.onerror = () => reject(req.error);
        });
    },

    async delete(id) {
        const db = await dbPromise;
        return new Promise((resolve, reject) => {
            const tx = db.transaction(STORE_NAME, 'readwrite');
            const store = tx.objectStore(STORE_NAME);
            const req = store.delete(id);
            req.onsuccess = () => resolve();
            req.onerror = () => reject(req.error);
        });
    },

    async initDefaults(initialData) {
        try {
            const current = await this.getAll();
            if (current.length === 0) {
                console.log("Seeding initial data...");
                for (const p of initialData) {
                    await this.save(p);
                }
                return initialData;
            }
            return current;
        } catch (e) {
            console.error("Init defaults failed", e);
            return [];
        }
    }
};

window.ProjectDB = ProjectDB; // Ensure global access
console.log("ProjectDB initialized", window.ProjectDB);
