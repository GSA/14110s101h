require('@uswds/uswds');

// gh-edit-page.js

// Sets the github URL link and button styles for each resource when edit-mode is enabled
// eslint-disable-next-line func-names

(function () {
  const githubEditLinks = document.querySelectorAll("[data-gh-edit-page]");
  const editToolsButton = document.querySelector(".gh-edit-tools");
  const repoBaseUrl = "https://github.com/chrisarrr/14110s101h";

  /**
   * Object for storing the git file edit path and branch
   */
  const gitRepo = {
    filepath: null,
    // eslint-disable-next-line no-use-before-define
    branch: setBranch(),
  };

  /**
   * If on cloud.pages get the branch name from the URL
   * Otherwise, use "main" for localhost and production
   * @returns {string} branch name
   * @example:
   * Given: https://federalist-466b7d92-5da1-4208-974f-d61fd4348571.sites.pages.cloud.gov/preview/gsa/digitalgov.gov/nl-site-alert-component/
   * Expect: nl-site-alert-component
   */
  function setBranch() {
    const host = window.location.hostname;
    let currentBranch = "";
    if (!host.includes("sites.pages.cloud.gov")) {
      currentBranch = "main";
    } else {
      // eslint-disable-next-line prefer-destructuring
      currentBranch = window.location.pathname.split("/")[4];
    }
    return currentBranch;
  }

  /**
   * Adds github "button" link and highlight style to Github items
   * Add link as last child in the parent element
   */
  function enableEditMode() {
    githubEditLinks.forEach((link) => {
      gitRepo.filepath = link.dataset.ghEditPage;
      const editSpan = Object.assign(document.createElement("span"), {
        classList: "gh-edit-page__button-text",
        textContent: "edit",
      });
      const editLinkButton = Object.assign(document.createElement("a"), {
        classList: "gh-edit-page__button",
        href: `${repoBaseUrl}/edit/${gitRepo.branch}/content/${gitRepo.filepath}`,
        target: "_blank",
        rel: "noreferrer",
        title: "edit page on github",
      });

      editLinkButton.appendChild(editSpan);
      link.appendChild(editLinkButton);
      link.classList.add("gh-edit-page");
    });
  }

  /**
   * Remove highlight style and edit button element from Github items
   * Removes the last child link from the parent element
   */
  function disableEditMode() {
    // eslint-disable-next-line func-names
    githubEditLinks.forEach((editLink) => {
      editLink.classList.remove("gh-edit-page");
      editLink.lastChild.remove();
    });
  }

  /**
   * Add event listener to the edit tools button in lower right corner
   */
  // eslint-disable-next-line func-names
  editToolsButton.addEventListener("click", function () {
    if (this.classList.contains("gh-edit-tools--active")) {
      disableEditMode();
      this.classList.remove("gh-edit-tools--active");
    } else {
      enableEditMode();
      this.classList.add("gh-edit-tools--active");
    }
  });
})();

// gh-edit-commit.js

/**
 * Sets the most recent commit timestamp for the page
 * This is displayed in div.gh-commit-info section at the bottom of the page
 */
(() => {
  const baseURL = `https://github.com/chrisarrr/14110s101h`;
  const apiURL = `https://api.github.com/repos/chrisarrr/14110s101h`;
  const editPageLink = document.querySelector(".gh-commit-info__container");

  /**
   * Object for storing the git file edit path and branch
   */
  const gitRepo = {
    // eslint-disable-next-line no-use-before-define
    filepath: setFilepath(),
    // eslint-disable-next-line no-use-before-define
    branch: setBranch(),
  };

  /**
   * Get hugo file path from the [data-gh-edit-page] attribute to link to Github repo location
   * @returns {string} hugo file path
   * @example
   * news/2023/07/2023-07-19-gsa-shared-service-provider-program-guide.md
   */
  function setFilepath() {
    if (!editPageLink) {
      return "";
    }

    return document
      .querySelector("[data-gh-edit-page]")
      .getAttribute("data-gh-edit-page");
  }

  /**
   * If on cloud.pages get the branch name from the URL
   * Otherwise, use "main" for localhost and production
   * @returns {string} branch name
   * @example:
   * Given: https://federalist-466b7d92-5da1-4208-974f-d61fd4348571.sites.pages.cloud.gov/preview/gsa/digitalgov.gov/nl-site-alert-component/
   * Expect: nl-site-alert-component
   */
  function setBranch() {
    const host = window.location.hostname;
    let currentBranch = "";
    if (!host.includes("sites.pages.cloud.gov")) {
      currentBranch = "main";
    } else {
      // eslint-disable-next-line prefer-destructuring
      currentBranch = window.location.pathname.split("/")[4];
    }
    return currentBranch;
  }

  /**
   * Takes a github ISO date format and converts it to a human friendly datetime string
   * @param {timezone} timezoneDate YYYY-MM-DDTHH:MM:SSZ
   * @returns {string} Formatted datetime string
   * @example
   *  returns string:
   *  "Jul 6, 2023 at 5:23 p.m., ET"
   */
  function formatDate(timezoneDate) {
    const inputDate = new Date(timezoneDate);

    const dateOptions = {
      day: "numeric",
      month: "short",
      year: "numeric",
    };

    const timeOptions = {
      hour: "numeric",
      minute: "2-digit",
      timeZone: "America/New_York",
      timeZoneName: "shortGeneric",
    };

    // `undefined` is used for the locales parameter, this option lets the local host determine the date formatting based on browser region location
    // https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Date/toLocaleDateString
    // https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Intl/DateTimeFormat/DateTimeFormat#locales
    const outputDate = inputDate.toLocaleDateString(undefined, dateOptions);
    const outputTime = inputDate
      .toLocaleTimeString("en-US", timeOptions)
      .replace("AM", "a.m.,")
      .replace("PM", "p.m.,");
    return `${outputDate} at ${outputTime}`;
  }

  /**
   * Retrieves Github API commit information for single hugo resource/page
   * Uses branchPath and gitRepo.filepath to build Github URL
   * @returns {string} commit date string — 2023-09-06T21:05:57Z
   */
  // eslint-disable-next-line consistent-return
  async function getCommitData() {
    const commitApiPath = `${apiURL}/commits/${gitRepo.branch}?path=/content/${gitRepo.filepath}`;

    if (commitApiPath !== undefined) {
      const githubResponse = await fetch(`${commitApiPath}`);

      if (!githubResponse.ok) {
        throw new Error(`HTTP error! status: ${githubResponse.status}`);
      }

      const githubData = await githubResponse.json();

      if (typeof githubData !== "undefined" || githubData.length !== 0) {
        let commitDate = Array.isArray(githubData) ? githubData[0] : githubData;
        commitDate = commitDate.commit.committer.date;
        return commitDate;
      }
    }
  }

  /**
   * Display the github commit date in div.gh-commit-info element
   * Creates and displays the markup for reading and editing the most recent commit date
   */
  async function displayGithubCommitLink() {
    const commitDate = await getCommitData();
    const commitHistoryUrl = `${baseURL}/commits/${gitRepo.branch}/content/${gitRepo.filepath}`;
    const gitEditFilePath = `${baseURL}/edit/${gitRepo.branch}/content/${gitRepo.filepath}`;

    const githubEditLink = Object.assign(document.createElement("a"), {
      classList: "usa-button usa-button--outline",
      href: `${gitEditFilePath}`,
      innerHTML: "Edit",
      target: "_blank",
      title: "Edit in GitHub",
    });

    const lastCommitParagraph = Object.assign(document.createElement("p"), {
      classList: "gh-commit-info__description",
      innerHTML: "Last updated on ",
    });

    const lastCommitLink = Object.assign(document.createElement("a"), {
      href: `${commitHistoryUrl}`,
    });

    const lastCommitSpan = Object.assign(document.createElement("span"), {
      classList: "gh-commit-info__timestamp",
      innerHTML: `${formatDate(commitDate)}`,
    });

    lastCommitLink.appendChild(lastCommitSpan);
    lastCommitParagraph.appendChild(lastCommitLink);

    const githubCommitFragment = new DocumentFragment();

    githubCommitFragment.appendChild(githubEditLink);
    githubCommitFragment.appendChild(lastCommitParagraph);

    // if on a page that has a div.gh-commit-info element
    if (editPageLink) {
      editPageLink.appendChild(githubCommitFragment);
    }
  }

  displayGithubCommitLink();
})();
