'use client';

import { useState, useEffect } from 'react';

export default function Home() {

  const [country, setCountry] = useState("France");
  const [skill, setSkill] = useState("Bollards");
  const [id, setID] = useState(0);
  const [weaknesses, setWeaknesses] = useState<{ id: any; country: string; skill: string }[]>([]);
  const [loading, setLoading] = useState(false);

  function handleSubmit(e: any) {
    e.preventDefault();
    console.log(country, skill);
    setID(prevId => {
      const newId = prevId + 1;
      setWeaknesses([
        ...weaknesses,
        { id: newId, country: country, skill: skill }
      ]);
      return newId;
    });
  }

  function handleDelete(id: any) {
    setWeaknesses(
      weaknesses.filter(a => (
        a.id !== id
      ))
    );
  }

  const handleCreation = async () => {
    setLoading(true);

    console.log(weaknesses);
    
    const response = await fetch("http://localhost:8080/", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ userWeaknesses: weaknesses })
    });

    setLoading(false);
  }

  return (
    <div
      className="flex flex-col items-center justify-items-center min-h-screen p-8 pb-20 gap-16 sm:p-20 w-full"
      style={{ backgroundImage: "url('/images/background.png')" }}
    >
      <img className='w-1/2' src="/images/geotrainr.png" />
      <div id="main" className="w-2/5 mx-auto">
        <div className="bg-white rounded-lg shadow-lg w-full font-bold p-4 flex flex-col justify-center items-center" id="rectangle">
          <h1 className="text-xl mt-2">Enter your weaknesses below:</h1>
          <div id="input" className="m-2 text-lg flex flex-col md:flex-row">
            <form className="flex" onSubmit={handleSubmit}>
              <label htmlFor="country"></label>
              <select id="country" name="country" onChange={e => (setCountry(e.target.value))}>
                <option value="France">France</option>
                <option value="Germany">Germany</option>
                <option value="United Kingdom">United Kingdom</option>
                <option value="Italy">Italy</option>
                <option value="Lithuania">Lithuania</option>
              </select>
              <select id="skill" name="skill" className="m-2" onChange={e => (setSkill(e.target.value))}>
                <option value="Bollards">Bollards</option>
                <option value="Road Lines">Road Lines</option>
                <option value="Signs">Signs</option>
              </select>
              <div className="w-full">
                <input name="submit" type="submit" className="m-2 bg-stone-300 hover:bg-stone-400 transition duration-200 rounded-full p-2 w-full"></input>
              </div>
            </form>
          </div>
          <div id="weaknesses" className="flex flex-col items-center justify-center text-center">
              <ul className="flex flex-col items-center justify-center"> 
                {weaknesses.map(weakness => (
                  <li className="flex m-3" key={weakness.id}>
                      <h1 className="bg-stone-300 rounded-full p-3 px-6">{weakness.country}, {weakness.skill}</h1>
                      <button onClick={e => handleDelete(weakness.id)} className="text-xl m-2">x</button>
                  </li>
                ))}
              </ul>
          </div>
        </div>
        <div className="flex flex-col justify-center items-center w-full">
          <button onClick={handleCreation} className="rounded-full shadow-lg p-3 w-1/2 text-white font-bold bg-linear-to-t from-lime-600 to-lime-300 m-6 text-xl hover:from-lime-700 transition duration-200">{loading ? "Creating Map..." : "Create Map!"}</button>
          <h3 className="text-white">Map creation may take a few minutes</h3>
        </div>
      </div>
    </div>
  );
}
