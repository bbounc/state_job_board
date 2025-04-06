import React from 'react';

const JobCard = ({ job }) => {
  return (
    <div className="job-card">
      <h2>{job.title}</h2>
      <p>{job.state}</p>
      <p>{job.deadline}</p>
      <p>{job.pay}</p>
      {job.link && (
        <a href={job.link} target="_blank" rel="noopener noreferrer" className="job-link-btn">
          View Job
        </a>
      )}
    </div>
  );
};

export default JobCard;
