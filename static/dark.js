/* dark.js – diagnostic build ------------------------------------- */
document.addEventListener('DOMContentLoaded', () => {

    const root = document.documentElement;
    const nav  = document.getElementById('main-nav');
    const btn  = document.getElementById('toggle-dark-mode');
  
    console.group('dark.js diagnostics');
    console.log('nav found :', !!nav, nav);
    console.log('btn found :', !!btn, btn);
    console.groupEnd();
  
    if (!nav || !btn){
      console.error('dark.js: toggle button or navbar not found – check IDs');
      return;
    }
  
    /* restore previous choice */
    if (localStorage.getItem('dark') === 'on'){
      root.classList.add('dark-mode');
      nav.classList.replace('navbar-light','navbar-dark');
      nav.classList.replace('bg-light','bg-dark');
    }
  
    /* click handler */
    btn.addEventListener('click', () => {
      const dark = root.classList.toggle('dark-mode');
      nav.classList.toggle('navbar-dark', dark);
      nav.classList.toggle('navbar-light', !dark);
      nav.classList.toggle('bg-dark',     dark);
      nav.classList.toggle('bg-light',    !dark);
      localStorage.setItem('dark', dark ? 'on' : 'off');
    });
  });
  