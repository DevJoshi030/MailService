// React Module Imports
import React, { useState, useEffect } from "react";

// Component Imports
import Header from "./Header";
import MailList from "./MailList";
import sentStyles from "../styles/sentStyles";
import checkIfLoggedIn from "../utils/checkIfLoggedIn";

const Sent = (props) => {
  const classes = sentStyles();

  const [effectFlag, setEffectFlag] = useState(false);
  const [mailData, setMailData] = useState({});

  checkIfLoggedIn().then((res) => (!res ? props.history.push("/") : null));

  useEffect(async () => {
    if (props.location.state) {
      props.location.state = null;
      return;
    }
    await fetch("/api/sent/")
      .then((res) => res.json())
      .then((data) => setMailData(data));
  }, [effectFlag]);

  const handleSearch = async (string) => {
    await fetch("/api/search/s-" + string + "/")
      .then((res) => {
        if (res.status === 400) return;
        return res.json();
      })
      .then((data) => (data ? setMailData(data) : null));
  };

  if (props.location.state) {
    handleSearch(props.location.state);
  }

  return (
    <div className={classes.root}>
      <Header
        history={props.history}
        search={handleSearch}
        resetReceived={() => {}}
        resetSent={() => setEffectFlag(!effectFlag)}
      />
      <main className={classes.content}>
        <div className={classes.toolbar} />
        <MailList
          {...props}
          data={mailData.data ? mailData.data.slice().reverse() : null}
          sender={false}
        />
      </main>
    </div>
  );
};

export default Sent;
