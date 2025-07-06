'use client';

import { useState, useEffect } from 'react';

export default function Home() {

  const [country, setCountry] = useState("Austria");
  const [skill, setSkill] = useState("Bollards");
  const [id, setID] = useState(0);
  const [weaknesses, setWeaknesses] = useState<{ id: number; country: string; skill: string }[]>([]);
  const [loading, setLoading] = useState(false);
  const [download, setDownload] = useState(false);
  const [submitted, setSubmitted] = useState(false);

  useEffect(() => {
    console.log("useEffect");
    if (weaknesses.length != 0) {
      setSubmitted(true);
    } else {
      setSubmitted(false);
    }
  }, [weaknesses])

  function handleSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    console.log(country, skill);
    console.log(id);
    setID(prevId => {
      const newId = prevId + 1;
      setWeaknesses([
        ...weaknesses,
        { id: newId, country: country, skill: skill }
      ]);
      return newId;
    });
  }

  function handleDelete(id: number) {
    setWeaknesses(
      weaknesses.filter(a => (
        a.id !== id
      ))
    );
  }

  const handleCreation = async () => {
    if (submitted) {
      try {
        setDownload(false)
        setLoading(true);

        console.log(weaknesses);

        const response = await fetch("https://geotrainr.onrender.com/", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({ userWeaknesses: weaknesses })
        });

        setLoading(false);
        setDownload(true);

        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = 'GeoTrainr-Map.json';
        a.click();
        window.URL.revokeObjectURL(url);

        setDownload(false);
      } catch (err) {
        setLoading(false);
      } 
    }
  }

  return (
    <div
      className="flex flex-col items-center justify-items-center min-h-screen bg-no-repeat p-8 pb-20 gap-16 sm:p-20 w-full bg-midnight"
      style={{ backgroundImage: "url('/images/background.png')" }}
    >
      <img className='w-1/2' src="/images/geotrainr.png" />
      <div id="main" className="w-full mx-auto flex flex-col justify-center items-center">
        <div className="bg-white rounded-lg shadow-lg w-2/5 font-bold p-4 flex flex-col justify-center items-center" id="rectangle">
          <h1 className="text-xl mt-2">Enter your weaknesses below:</h1>
          <div id="input" className="m-2 text-lg flex flex-col md:flex-row">
            <form className="flex flex-col md:flex-row" onSubmit={handleSubmit}>
              <label htmlFor="country"></label>
              <select id="country" name="country" onChange={e => (setCountry(e.target.value))}>
                <option value="France">Austria</option>
                <option value="Germany">Belgium</option>
                <option value="United Kingdom">Bulgaria</option>
                <option value="Italy">Czechia</option>
                <option value="Denmark">Denmark</option>
                <option value="Estonia">Estonia</option>
                <option value="Finland">Finland</option>
                <option value="France">France</option>
                <option value="Germany">Germany</option>
                <option value="Hungary">Hungary</option>
                <option value="Iceland">Iceland</option>
                <option value="Ireland">Ireland</option>
                <option value="Italy">Italy</option>
                <option value="Lithuania">Lithuania</option>
                <option value="Netherlands">Netherlands</option>
                <option value="Norway">Norway</option>
                <option value="Poland">Poland</option>
                <option value="Portugal">Portugal</option>
                <option value="Romania">Romania</option>
                <option value="Russia">Russia</option>
                <option value="Spain">Spain</option>
                <option value="Sweden">Sweden</option>
                <option value="Switzerland">Switzerland</option>
                <option value="Ukraine">Ukraine</option>
                <option value="United Kingdom">United Kingdom</option>
              </select>
              <select id="skill" name="skill" className="m-2" onChange={e => (setSkill(e.target.value))}>
                <option value="Bollards">Bollards</option>
                {/* <option value="Road Lines">Road Lines</option>
                <option value="Signs">Signs</option> */}
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
                      <button onClick={() => handleDelete(weakness.id)} className="text-xl m-2">x</button>
                  </li>
                ))}
              </ul>
          </div>
        </div>
        <div className="flex flex-col justify-center items-center w-full">
          <button id="create-button" onClick={handleCreation} className="rounded-full shadow-lg p-3 w-1/3 text-white font-bold bg-linear-to-t from-lime-600 to-lime-300 m-6 text-xl hover:from-lime-700 transition duration-200">{loading ? "Creating Map..." : download ? "Downloading..." : submitted ? "Create Map!" : "Please select a country + skill"}</button>
          {/* <h3 className="text-red-400 mb-4 text-xl font-bold">PLEASE ALLOW FOR SOME ERROR, THIS IS IN BETA</h3> */}
          <h3 className="text-red-400 mb-4 text-sm">Map creation takes 2000 samples and may take up to 8 minutes to process per country</h3>
          <h3 className='text-red-400 mb-4 text-sm'>Generated maps will include country selected and surrounding countries to help you practice</h3>
          <h3 className='text-red-400 mb-4 text-sm'>Generated maps will not be evenly distributed within the country selected</h3>

        </div>
        <div id="faq" className='mt-10 text-white flex flex-col justify-center items-center text-xl w-full overflow-x-hidden'>
          <details className='m-4 flex flex-col text-center items-center w-full'>
            <summary>How do I upload a GeoTrainr map to Geoguessr?</summary>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6 w-2/3 mt-6 max-w-2/3 overflow-x-hidden justify-items-center mx-auto">
              {[
          {
            text: 'Click "My Maps" on your Geoguessr profile and select "Create New Map"',
            img: "/images/step1.png",
          },
          {
            text: 'Select "Handpicked Locations" for the type of map',
            img: "/images/step2.png",
          },
          {
            text: 'Click the three dots on the top right hand corner. Then, select "import json file". From there, then select the downloaded "GeoTrainr Map" json file.',
            img: "/images/step3.png",
          },
          {
            text: 'After the locations have been uploaded, press "Save and Publish". Now you can play your map!',
            img: "/images/step4.png",
          },
              ].map((step, idx) => (
          <div key={idx} className="flex flex-col w-full items-center bg-white/80 rounded-lg shadow p-4">
            <h1 className="mb-4 text-base font-semibold text-gray-800 text-center">{step.text}</h1>
            <div className="w-full flex justify-center">
              <img
                src={step.img}
                alt={`Step ${idx + 1}`}
                className="object-contain w-full max-w-[220px] aspect-video rounded"
              />
            </div>
          </div>
              ))}
            </div>
          </details>
          <details className='m-4 flex flex-col text-center items-center w-2/3'>
              <summary>How does GeoTrainr work?</summary>
              <p className='mt-4'>GeoTrainr uses a yolov5 model to go through different images pulled from Mapillary in the selected countries
                and detects if they have the user&apos;s selected weaknesses. After the model cycles through everything, a list of all detections&apos; coordinates
                is returned. Then, these coordiantes are compiled into a json file that the user can download.
              </p>
          </details>
        </div>
      </div>
    </div>
  );
}
