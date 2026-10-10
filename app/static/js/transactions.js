"use strict";
document.documentElement.classList.add('tx-enhanced');
// Integer cents with BigInt: preview never changes the authoritative backend total.
const txForm = document.querySelector('[data-transaction-form]');
if (txForm) {
  const prices = JSON.parse(txForm.dataset.prices);
  const container = txForm.querySelector('[data-lines]');
  let nextIndex = Math.max(...Array.from(container.querySelectorAll('[data-product]'),select=>Number(select.name.split('-')[1])))+1;
  const pattern = container.firstElementChild.cloneNode(true);
  function cents(value) {
    if (!/^\d+(?:\.\d{1,2})?$/.test(value)) return null;
    const [whole,part=''] = value.split('.');
    return BigInt(whole)*100n + BigInt(part.padEnd(2,'0'));
  }
  function vnd(value) {
    return (value/100n).toString().replace(/\B(?=(\d{3})+(?!\d))/g,'.') + ',' + (value%100n).toString().padStart(2,'0') + ' ₫';
  }
  function update() {
    let total=0n, valid=true;
    container.querySelectorAll('[data-line]').forEach(line => {
      const selection=line.querySelector('[data-product]').value;
      const info=prices[selection];
      const qty=line.querySelector('[data-quantity]').value;
      line.querySelector('[data-stock]').textContent=info ? 'Tồn kho hiện tại: '+info.stock : '';
      if (line.querySelector('[data-price]')) line.querySelector('[data-price]').textContent=info ? vnd(cents(info.price)) : 'Chọn sản phẩm';
      const unit=cents(txForm.dataset.kind === 'purchases' ? line.querySelector('[data-cost]').value : info?.price || '');
      const ok=info && unit!==null && /^\d+$/.test(qty) && BigInt(qty)>0n;
      line.querySelector('[data-line-total]').textContent=ok ? vnd(unit*BigInt(qty)) : '—';
      if(ok)total+=unit*BigInt(qty); else valid=false;
      line.querySelector('[data-remove]').disabled=container.children.length===1;
    });
    txForm.querySelector('[data-grand-total]').textContent=valid ? vnd(total) : '—';
    txForm.querySelector('[data-add-line]').disabled=container.children.length>=50;
  }
  container.addEventListener('input',update);
  container.addEventListener('change',event=>{
    if(event.target.matches('[data-product]')) {
      const line=event.target.closest('[data-line]');
      if(line.querySelector('[data-cost]'))line.querySelector('[data-cost]').value=prices[event.target.value]?.price || '';
    }
    update();
  });
  container.addEventListener('click',event=>{
    if(event.target.closest('[data-remove]') && container.children.length>1){event.target.closest('[data-line]').remove();update();}
  });
  txForm.querySelector('[data-add-line]').addEventListener('click',()=>{
    if(container.children.length>=50)return;
    const line=pattern.cloneNode(true), index=nextIndex++;
    line.querySelectorAll('[name],[id],[for]').forEach(element=>{
      for(const attr of ['name','id','for'])if(element.hasAttribute(attr))element.setAttribute(attr,element.getAttribute(attr).replace(/lines-\d+-/g,'lines-'+index+'-'));
    });
    line.querySelectorAll('input').forEach(input=>input.value=input.matches('[data-quantity]') ? '1' : '');
    line.querySelector('[data-product]').value='0';
    line.querySelectorAll('.catalog-field-error').forEach(error=>error.remove());
    container.append(line);update();line.querySelector('select').focus();
  });
  let timer, controller;
  txForm.querySelector('[data-product-search]').addEventListener('input',event=>{
    clearTimeout(timer);controller?.abort();
    const q=event.target.value;
    timer=setTimeout(async()=>{
      controller=new AbortController();
      const status=txForm.querySelector('[data-search-status]');status.textContent='Đang tìm sản phẩm…';
      try{
        const response=await fetch(txForm.dataset.optionsUrl+'?q='+encodeURIComponent(q),{signal:controller.signal});
        if(!response.ok)throw new Error();
        const rows=await response.json();
        rows.forEach(row=>prices[row.id]={price:row.price,stock:row.stock});
        for(const select of container.querySelectorAll('[data-product]')){
          const chosen=select.selectedOptions[0]?.cloneNode(true), value=select.value;
          select.replaceChildren(new Option('Chọn sản phẩm','0'));
          rows.forEach(row=>select.add(new Option(row.label,String(row.id))));
          if(chosen && value!=='0' && !rows.some(row=>String(row.id)===value))select.append(chosen);
          select.value=value;
        }
        // Future new rows should use the latest search results.
        pattern.querySelector('[data-product]').replaceChildren(...container.querySelector('[data-product]').cloneNode(true).children);
        status.textContent=rows.length ? rows.length+' lựa chọn (tối đa 50). Sản phẩm đã chọn được giữ lại.' : 'Không tìm thấy sản phẩm đang hoạt động.';
        update();
      }catch(error){if(error.name!=='AbortError')status.textContent='Không thể tìm sản phẩm. Vui lòng thử lại.';}
    },300);
  });
  update();
}
document.querySelector('#transaction-confirm')?.addEventListener('show.bs.modal',event=>{
  const trigger=event.relatedTarget;
  event.target.querySelector('[data-confirm-message]').textContent=trigger.dataset.message;
  event.target.querySelector('[data-confirm-form]').action=trigger.dataset.url;
});
