// Import the functions you need from the SDKs you need
import { initializeApp } from "firebase/app";
import { getAnalytics } from "firebase/analytics";
import { getAuth } from "firebase/auth";
// TODO: Add SDKs for Firebase products that you want to use
// https://firebase.google.com/docs/web/setup#available-libraries

// Your web app's Firebase configuration
// For Firebase JS SDK v7.20.0 and later, measurementId is optional
const firebaseConfig = {
  apiKey: "AIzaSyC5HyqIqcbC72bi6reW5O5DgiuFjNm6qX4",
  authDomain: "socialpjt.firebaseapp.com",
  projectId: "socialpjt",
  storageBucket: "socialpjt.firebasestorage.app",
  messagingSenderId: "344559245905",
  appId: "1:344559245905:web:d494d3fecbadc9091d3670",
  measurementId: "G-NBD5GFLHL0",
};

// Initialize Firebase
const app = initializeApp(firebaseConfig);
const analytics = getAnalytics(app);
const auth = getAuth(app);

export { app, analytics, auth };
