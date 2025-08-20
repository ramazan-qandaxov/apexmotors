let currentSlide = 0;

function moveSlide(direction, slides) {
  const totalSlides = slides.length;

  const current = slides[currentSlide];
  current.style.opacity = 0;
  current.style.zIndex = 0;

  setTimeout(() => {
    current.classList.remove('active');

    currentSlide = (currentSlide + direction + totalSlides) % totalSlides;

    const next = slides[currentSlide];
    next.classList.add('active');
    next.style.zIndex = 1;
    next.style.opacity = 1;
  }, 300);
}

document.addEventListener("DOMContentLoaded", () => {
  const slides = document.querySelectorAll('.carousel-item');

  if (slides.length === 0) return;

  slides[0].style.opacity = 1;
  slides[0].style.zIndex = 1;

  // Bind moveSlide to window so HTML buttons can call it
  window.moveSlide = (dir) => moveSlide(dir, slides);
});
