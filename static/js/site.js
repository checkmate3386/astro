(() => {
  const menuToggle = document.querySelector(".menu-toggle");
  const mainNav = document.querySelector("#main-nav");
  if (menuToggle && mainNav) {
    menuToggle.addEventListener("click", () => {
      const isOpen = menuToggle.getAttribute("aria-expanded") === "true";
      menuToggle.setAttribute("aria-expanded", String(!isOpen));
      mainNav.classList.toggle("is-open", !isOpen);
    });
  }

  const slides = [...document.querySelectorAll(".slide")];
  const dots = [...document.querySelectorAll(".carousel-dot")];
  const carousel = document.querySelector(".carousel");
  if (slides.length && dots.length) {
    let activeIndex = 0;
    let timer = null;
    let paused = false;
    const showSlide = (index) => {
      activeIndex = (index + slides.length) % slides.length;
      slides.forEach((slide, i) => {
        slide.hidden = i !== activeIndex;
        slide.classList.toggle("is-active", i === activeIndex);
      });
      dots.forEach((dot, i) => {
        dot.classList.toggle("is-active", i === activeIndex);
        dot.setAttribute("aria-pressed", String(i === activeIndex));
      });
    };
    const start = () => {
      if (timer || slides.length < 2 || paused) return;
      timer = window.setInterval(() => showSlide(activeIndex + 1), 5000);
    };
    const stop = () => {
      if (timer) window.clearInterval(timer);
      timer = null;
    };
    dots.forEach((dot) => {
      dot.addEventListener("click", () => {
        showSlide(Number(dot.dataset.slideIndex));
        stop();
        start();
      });
    });
    if (carousel) {
      carousel.addEventListener("mouseenter", () => { paused = true; stop(); });
      carousel.addEventListener("mouseleave", () => { paused = false; start(); });
      carousel.addEventListener("focusin", () => { paused = true; stop(); });
      carousel.addEventListener("focusout", () => { paused = false; start(); });
    }
    showSlide(0);
    start();
  }

  document.querySelectorAll("[data-registration-form]").forEach((form) => {
    const countField = form.querySelector('[name="people_count"]');
    const emailField = form.querySelector('[name="email"]');
    const emailConfirmField = form.querySelector('[name="email_confirm"]');
    const participantCards = [...form.querySelectorAll("[data-participant]")];
    const equipmentCheckbox = form.querySelector('[name="brings_equipment"]');
    const equipmentBlock = form.querySelector("[data-equipment-description]");

    const updateMinor = (card) => {
      const index = card.dataset.index;
      const checkbox = card.querySelector(`[name="is_minor_${index}"]`);
      const age = card.querySelector(`[name="age_${index}"]`);
      const ageField = age.closest(".age-field");
      ageField.hidden = !checkbox.checked;
      age.disabled = !checkbox.checked;
      age.required = checkbox.checked;
    };
    const updateEquipment = () => {
      if (!equipmentCheckbox || !equipmentBlock) return;
      equipmentBlock.hidden = !equipmentCheckbox.checked;
      const textarea = equipmentBlock.querySelector("textarea");
      textarea.disabled = !equipmentCheckbox.checked;
      textarea.required = equipmentCheckbox.checked;
    };
    const visibleCards = () => participantCards.filter((card) => !card.hidden);
    const setCount = (count) => {
      participantCards.forEach((card, index) => {
        card.hidden = index >= count;
        const firstName = card.querySelector(`[name="first_name_${index}"]`);
        const lastName = card.querySelector(`[name="last_name_${index}"]`);
        firstName.required = index < count;
        lastName.required = index < count;
        updateMinor(card);
      });
    };

    if (countField) {
      let previousCount = Number(countField.value);
      countField.addEventListener("change", () => {
        const nextCount = Number(countField.value);
        const removedCards = participantCards.slice(nextCount, previousCount);
        const hasData = removedCards.some((card) =>
          [...card.querySelectorAll("input, select")].some((field) =>
            field.type === "checkbox" ? field.checked : Boolean(field.value),
          ),
        );
        if (nextCount < previousCount && hasData &&
            !window.confirm("Les informations des participants retirés seront perdues. Continuer ?")) {
          countField.value = String(previousCount);
          return;
        }
        removedCards.forEach((card) => {
          card.querySelectorAll("input, select").forEach((field) => {
            if (field.type === "checkbox") field.checked = false;
            else field.value = "";
          });
        });
        previousCount = nextCount;
        setCount(nextCount);
      });
      setCount(previousCount);
    }

    participantCards.forEach((card) => {
      const minorCheckbox = card.querySelector('[type="checkbox"]');
      minorCheckbox.addEventListener("change", () => updateMinor(card));
      const removeButton = card.querySelector("[data-remove-participant]");
      if (!removeButton) return;
      removeButton.addEventListener("click", () => {
        const visible = visibleCards();
        if (visible.length === 1) {
          if (window.confirm("Supprimer cette personne et toute l’inscription ?")) {
            const deleteForm = document.querySelector("[data-delete-form]");
            if (deleteForm) deleteForm.requestSubmit();
          }
          return;
        }
        const index = visible.indexOf(card);
        const count = visible.length;
        const removedHasData = [...card.querySelectorAll("input, select")].some((field) =>
          field.type === "checkbox" ? field.checked : Boolean(field.value),
        );
        if (removedHasData && !window.confirm("Supprimer les informations de ce participant ?")) {
          return;
        }
        for (let position = index; position < count - 1; position += 1) {
          const current = visible[position];
          const next = visible[position + 1];
          ["first_name", "last_name", "is_minor", "age"].forEach((fieldName) => {
            const currentField = current.querySelector(`[name="${fieldName}_${position}"]`);
            const nextField = next.querySelector(`[name="${fieldName}_${position + 1}"]`);
            if (currentField.type === "checkbox") currentField.checked = nextField.checked;
            else currentField.value = nextField.value;
          });
        }
        const lastCard = visible[count - 1];
        lastCard.querySelectorAll("input, select").forEach((field) => {
          if (field.type === "checkbox") field.checked = false;
          else field.value = "";
        });
        countField.value = String(count - 1);
        previousCount = count - 1;
        setCount(previousCount);
      });
    });

    if (equipmentCheckbox) {
      equipmentCheckbox.addEventListener("change", updateEquipment);
      updateEquipment();
    }

    const validateEmailConfirmation = () => {
      const emailsMatch = emailField.value.trim().toLowerCase() ===
        emailConfirmField.value.trim().toLowerCase();
      emailConfirmField.setCustomValidity(
        emailsMatch ? "" : "Les deux adresses e-mail doivent être identiques.",
      );
    };
    emailField.addEventListener("input", validateEmailConfirmation);
    emailConfirmField.addEventListener("input", validateEmailConfirmation);
    form.addEventListener("submit", (event) => {
      validateEmailConfirmation();
      if (!form.reportValidity()) event.preventDefault();
    });
  });

  document.querySelectorAll("[data-confirm-delete]").forEach((button) => {
    button.addEventListener("click", (event) => {
      if (!window.confirm("Supprimer définitivement cette inscription ?")) {
        event.preventDefault();
      }
    });
  });

  document.querySelectorAll('[role="tab"][data-tab]').forEach((tab) => {
    tab.addEventListener("click", () => {
      document.querySelectorAll('[role="tab"][data-tab]').forEach((item) => {
        const selected = item === tab;
        item.setAttribute("aria-selected", String(selected));
        document.querySelector(`#panel-${item.dataset.tab}`).hidden = !selected;
      });
    });
  });
})();
