"use strict";
const customerPicker=document.querySelector('[data-customer-picker]');
if(customerPicker){
  const mode=document.querySelector('#customer_mode'), selected=document.querySelector('#customer_id');
  const options=JSON.parse(customerPicker.dataset.customerOptions), status=customerPicker.querySelector('[data-customer-status]');
  const history=customerPicker.querySelector('[data-customer-history]'), results=customerPicker.querySelector('[data-customer-results]');
  const fields={name:document.querySelector('#customer_name'),phone:document.querySelector('#customer_phone'),email:document.querySelector('#customer_email'),address:document.querySelector('#customer_address')};
  let lastSelected=null;
  function update(){
    const customer=mode.value==='existing' ? options[selected.value] : null;
    selected.disabled=mode.value!=='existing';
    for(const [name,field] of Object.entries(fields)){
      field.readOnly=!!customer;
      if(customer)field.value=customer[name]||'';
      else if(lastSelected)field.value='';
    }
    history.hidden=!customer;
    if(customer)history.href=customer.history_url;else history.removeAttribute('href');
    status.textContent=customer ? 'Đã chọn '+customer.name+'. Backend đọc lại hồ sơ active khi lưu.' : mode.value==='new' ? 'Lưu hồ sơ mới cùng bản nháp trong một transaction. Số trùng sẽ bị từ chối.' : mode.value==='existing' ? 'Hãy chủ động chọn đúng hồ sơ trước khi lưu.' : 'Khách vãng lai: không lưu hồ sơ hoặc tự liên kết, kể cả số điện thoại đã có.';
    lastSelected=customer||null;
  }
  selected.addEventListener('change',update);mode.addEventListener('change',update);update();
  let timer,controller;
  customerPicker.querySelector('[data-customer-search]').addEventListener('input',event=>{
    clearTimeout(timer);controller?.abort();results.replaceChildren();
    const q=event.target.value.trim();if(q.length<2)return;
    timer=setTimeout(async()=>{
      controller=new AbortController();status.textContent='Đang tìm khách hàng…';
      try{
        const response=await fetch(customerPicker.dataset.searchUrl+'?q='+encodeURIComponent(q),{signal:controller.signal});
        if(!response.ok)throw new Error();
        const rows=await response.json();results.replaceChildren();
        rows.forEach(customer=>{
          options[customer.id]=customer;
          const button=document.createElement('button');button.type='button';button.className='btn btn-light';
          const title=document.createElement('strong');title.textContent=customer.name;
          const contact=document.createElement('small');contact.textContent=customer.phone;
          button.append(title,contact);
          button.addEventListener('click',()=>{
            if(!Array.from(selected.options).some(option=>option.value===String(customer.id)))selected.add(new Option(customer.name+' · '+customer.phone,String(customer.id)));
            mode.value='existing';selected.value=String(customer.id);results.replaceChildren();update();
          });results.append(button);
        });
        status.textContent=rows.length ? rows.length+' hồ sơ phù hợp (tối đa 20). Chọn để liên kết hoặc xem lịch sử.' : 'Không tìm thấy khách active. Có thể tạo mới hoặc bán vãng lai.';
      }catch(error){if(error.name!=='AbortError')status.textContent='Không thể tìm khách hàng. Vui lòng thử lại.';}
    },300);
  });
}
