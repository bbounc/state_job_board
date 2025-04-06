import React, { useEffect, useState, useMemo } from 'react';
import axios from 'axios';
import Select from 'react-select';
import Fuse from 'fuse.js';
import { stateOptions } from './stateOptions';
import './App.css';
import { useCallback } from 'react';

const API_URL = process.env.REACT_APP_BACKEND_URL;



// parsePay helper...
function parsePay(payStr) {
  if (!payStr || payStr.toLowerCase() === 'n/a') return 0;
  const clean = payStr.replace(/\$|,/g, '').toLowerCase();
  if (clean.includes('-')) {
    const [low, high] = clean.split('-').map(s =>
      parseFloat(s.replace('k', '')) * (s.includes('k') ? 1000 : 1)
    );
    return (low + high) / 2;
  }
  let num = parseFloat(clean.replace('k', '')) * (clean.includes('k') ? 1000 : 1);
  return isNaN(num) ? 0 : num;
}

// Helper to parse and compare deadlines
function parseDeadline(deadline) {
  if (!deadline || deadline.toLowerCase() === 'na') return 'na';  // If deadline is NA, return a special identifier
  const date = new Date(deadline);
  if (isNaN(date.getTime())) return 'invalid'; // Non-numeric or invalid date
  return date;  // Valid date, return it as a Date object
}

function App() {
  const [allJobs, setAllJobs] = useState([]);
  const [jobs, setJobs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const [searchTerm, setSearchTerm] = useState('');
  const [stateFilter, setStateFilter] = useState([]);
  const [payFilter, setPayFilter] = useState('');
  const [sortOption, setSortOption] = useState('');  

  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);

  // Fetch and apply filters
  const fetchJobs = useCallback(async () => {
    setLoading(true);
    try {
      const resp = await axios.get(`${API_URL}/jobs`, {
        params: {
          skip: 0,
          limit: 1000,
          state: stateFilter.map(s => s.value).join(','),
        },
      });
      let data = resp.data;
      // pay filter
      if (payFilter) {
        const [minStr, maxStr] = payFilter.split('-');
        const min = parsePay(minStr), max = maxStr ? parsePay(maxStr) : Infinity;
        data = data.filter(j => {
          const p = parsePay(j.pay);
          return p >= min && p <= max;
        });
      }
      setAllJobs(data);
      setPage(1);
    } catch {
      setError('Error fetching jobs');
    } finally {
      setLoading(false);
    }
  }, [stateFilter, payFilter]);
  
  // And then use it in useEffect like this:
  useEffect(() => {
    fetchJobs();
  }, [fetchJobs]);  // This ensures fetchJobs is memoized and stable
   

  // Fuse for fuzzy title search
  const fuse = useMemo(() => new Fuse(allJobs, {
    keys: ['title'], threshold: 0.3, distance: 100
  }), [allJobs]);

  // Apply searchTerm + sorting + pagination
  useEffect(() => {
    let results = searchTerm
      ? fuse.search(searchTerm).map(r => r.item)
      : [...allJobs];

    // Apply sorting
    switch (sortOption) {
      case 'state-asc':
        results.sort((a,b)=>a.state.localeCompare(b.state));
        break;
      case 'state-desc':
        results.sort((a,b)=>b.state.localeCompare(a.state));
        break;
      case 'pay-asc':
        results.sort((a,b)=>parsePay(a.pay)-parsePay(b.pay));
        break;
      case 'pay-desc':
        results.sort((a,b)=>parsePay(b.pay)-parsePay(a.pay));
        break;
      case 'title-asc':
        results.sort((a,b)=>a.title.localeCompare(b.title));
        break;
      case 'title-desc':
        results.sort((a,b)=>b.title.localeCompare(a.title));
        break;
      case 'deadline-asc':
        results.sort((a,b) => {
          const deadlineA = parseDeadline(a.deadline);
          const deadlineB = parseDeadline(b.deadline);

          if (deadlineA === 'invalid' || deadlineB === 'invalid') {
            return deadlineA === 'invalid' ? -1 : 1;
          }

          if (deadlineA === 'na' && deadlineB !== 'na') return 1;  // "NA" should be second to last
          if (deadlineB === 'na' && deadlineA !== 'na') return -1;

          // Compare valid date deadlines
          if (deadlineA instanceof Date && deadlineB instanceof Date) {
            return deadlineA - deadlineB;  // Sort dates in ascending order (soonest first)
          }

          return 0; // Fallback if dates are identical or both "NA"
        });
        break;
       
        case 'deadline-desc':
          results.sort((a, b) => {
            // Helper function to parse deadline and handle special cases (NA, invalid)
            const parseDeadline = (deadline) => {
              if (deadline === 'NA') return 'na'; // Handle "NA"
              const parsedDate = new Date(deadline);
              return isNaN(parsedDate) ? 'invalid' : parsedDate; // Return 'invalid' for bad date formats
            };
        
            const deadlineA = parseDeadline(a.deadline);
            const deadlineB = parseDeadline(b.deadline);
        
            // Handle invalid dates: invalid dates go last
            if (deadlineA === 'invalid' || deadlineB === 'invalid') {
              return deadlineA === 'invalid' ? 1 : -1;
            }
        
            // Handle "NA" deadlines: NA comes last in this case
            if (deadlineA === 'na' && deadlineB !== 'na') return 1;
            if (deadlineB === 'na' && deadlineA !== 'na') return -1;
        
            // Now we compare valid date objects
            const dateA = new Date(deadlineA);
            const dateB = new Date(deadlineB);
        
            // Case 1: Both dates are in the future, sort by latest
            if (dateA >= new Date() && dateB >= new Date()) {
              return dateB - dateA; // Descending order (latest first)
            }
        
            // Case 2: One is in the future, the other in the past, future comes first
            if (dateA >= new Date() && dateB < new Date()) return -1;
            if (dateB >= new Date() && dateA < new Date()) return 1;
        
            // Case 3: Both are past dates, sort by latest (most recent first)
            return dateB - dateA; // Descending order (latest first)
          });
          break;
        


      default:
        break;
    }

    // paginate
    const start = (page-1)*10;
    setTotalPages(Math.ceil(results.length/10));
    setJobs(results.slice(start, start+10));
  }, [allJobs, searchTerm, fuse, sortOption, page]);

  useEffect(() => { fetchJobs(); }, [fetchJobs]);  // Corrected dependency array


  // Handlers
  const handleStateChange = sel => setStateFilter(sel||[]);
  const handlePayChange = e => setPayFilter(e.target.value);
  const handleSortChange = e => { setSortOption(e.target.value); setPage(1); };

  return (
    <div className="container">
      <header><h1>Job Listings</h1></header>

      <div className="search-bar">
        <input
          placeholder="Search jobs..."
          value={searchTerm}
          onChange={e=>{setSearchTerm(e.target.value); setPage(1);}}
        />

        <Select
          isMulti value={stateFilter}
          onChange={handleStateChange}
          options={stateOptions}
          placeholder="States..."
        />

        <select value={payFilter} onChange={handlePayChange}>
          <option value="">All Pay</option>
          <option value="0-50000">0–50k</option>
          <option value="50000-70000">50–70k</option>
          <option value="70000-90000">70–90k</option>
          <option value="90000-110000">90–110k</option>
          <option value="110000-9999999">110k+</option>
        </select>

        <select value={sortOption} onChange={handleSortChange}>
          <option value="">Sort By</option>
          <option value="state-asc">State A→Z</option>
          <option value="state-desc">State Z→A</option>
          <option value="pay-desc">Salary High→Low</option>
          <option value="pay-asc">Salary Low→High</option>
          <option value="title-asc">Title A→Z</option>
          <option value="title-desc">Title Z→A</option>
          <option value="deadline-asc">Deadline Soonest→Latest</option>
          <option value="deadline-desc">Deadline Latest→Soonest</option>
        </select>

        <button onClick={()=>{setPage(1);fetchJobs();}}>Refresh</button>
      </div>

      {loading? <p>Loading…</p> : error? <p>{error}</p> : (
        <>
          <div className="job-listings">
            {jobs.map(j=>(
              <div key={j.id} className="job-card">
                <h2>{j.title}</h2>
                <p>State: {j.state}</p>
                <p>Deadline: {j.deadline}</p>
                <p>Pay: {j.pay}</p>
                {j.link && <a href={j.link} target="_blank" rel="noopener noreferrer" className="job-link-btn">View Job</a>}
              </div>
            ))}
          </div>
          <div className="pagination">
            <button onClick={()=>setPage(p=>Math.max(p-1,1))} disabled={page===1}>Previous</button>
            <span> Page {page} of {totalPages} </span>
            <button onClick={()=>setPage(p=>Math.min(p+1,totalPages))} disabled={page===totalPages}>Next</button>
          </div>
        </>
      )}
    </div>
  );
}

export default App;
